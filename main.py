import os
import json
import sys
import io
import traceback
import re
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import Tool
from pypdf import PdfReader
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
app = FastAPI()

# --- DEFINING TOOLS (Updated) ---
tools_schema = [
    {
        "name": "get_service_price",
        "description": "Check service price.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"service_name": {"type": "STRING"}},
            "required": ["service_name"]
        }
    },
    {
        "name": "calculate_lead_score",
        "description": "Calculate VIP score.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "client_name": {"type": "STRING"},
                "industry": {"type": "STRING"}
            },
            "required": ["client_name", "industry"]
        }
    },
    {
        "name": "save_qualified_lead", # <--- NEW
        "description": "Save approved lead to database.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "client_name": {"type": "STRING"},
                "service": {"type": "STRING"},
                "score": {"type": "INTEGER"}
            },
            "required": ["client_name", "service", "score"]
        }
    }
]


tools = Tool(function_declarations=tools_schema)
model = genai.GenerativeModel('gemini-2.5-flash', tools=[tools])

# --- GENERIC MCP CALLER ---
async def call_mcp_generic(tool_name: str, arguments: dict):
    # Absolute path is safer
    script_path = os.path.abspath("tools_server.py")
    
    # Use sys.executable to ensure we use the same VENV Python
    server_params = StdioServerParameters(command=sys.executable, args=[script_path], env=None)
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # 10s timeout is plenty for local logic
                result = await asyncio.wait_for(
                    session.call_tool(tool_name, arguments=arguments), 
                    timeout=10.0
                )
                if result and result.content:
                    return result.content[0].text
                return "Error: No content."
    except Exception as e:
        return f"Tool Error: {str(e)}"

def clean_json_string(text):
    if not text: return ""
    text = text.replace("```json", "").replace("```", "").strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else text

@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    try:
        content = await file.read()
        pdf_reader = PdfReader(io.BytesIO(content))
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text() + "\n"

        # --- THE PROMPT ---
        prompt = f"""
        You are an Autonomous Sales Agent.
        RFP Content:
        {text_content}

        EXECUTION PLAN:
        1. Extract Client Name & Service.
        2. CALL 'get_service_price'.
        3. CALL 'calculate_lead_score'.
        
        DECISION LOGIC:
        - If Price is found AND Score > 10 -> Status is 'approved'.
        - If Price is missing  -> Status is 'declined'.
        
        CRITICAL ACTION:
        - IF (and ONLY IF) the status is 'approved', you MUST CALL 'save_qualified_lead' to record them in the DB.
        
        FINAL OUTPUT SCHEMA (JSON ONLY):
        {{
            "status": "approved" or "declined",
            "client_name": "...",
            "detected_service": "...",
            "lead_score": 0,
            "crm_action": "Saved to DB ID #..." or "Not Saved",
            "draft_email": "..."
        }}
        """

        chat = model.start_chat(enable_automatic_function_calling=False)
        response = chat.send_message(prompt)
        
        final_text = ""
        
        # --- THE RE-ACT LOOP ---
        loop_count = 0
        while loop_count < 5: # Safety break
            loop_count += 1
            if not response.parts: break

            part = response.parts[0]
            
            if part.function_call:
                fc = part.function_call
                t_name = fc.name
                t_args = dict(fc.args)
                
                print(f"🤖 Tool Call: {t_name} -> {t_args}")
                
                # Execute Tool
                tool_result = await call_mcp_generic(t_name, t_args)
                print(f"✅ Result: {tool_result}")
                
                # Send result back
                response = chat.send_message(
                    {
                        "role": "function",
                        "parts": [{"function_response": {"name": t_name, "response": {"result": tool_result}}}]
                    }
                )
            else:
                final_text = response.text
                break

        # --- FINAL CLEANUP ---
        if not final_text: raise ValueError("AI returned empty text.")
        
        try:
            return json.loads(clean_json_string(final_text))
        except:
            # Last resort self-correction
            correction = chat.send_message("Output ONLY the valid JSON object.")
            return json.loads(clean_json_string(correction.text))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)