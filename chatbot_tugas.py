# Import the necessary libraries
import streamlit as st  # For creating the web app interface
import os
from langchain_google_genai import ChatGoogleGenerativeAI  # For interacting with Google Gemini via LangChain
from langgraph.prebuilt import create_react_agent  # For creating a ReAct agent
from langchain_core.messages import HumanMessage, AIMessage  # For message formatting
from langchain_core.tools import tool  # For creating tools

# Import our database tools (harus ada di proyek: inisialisasi, konversi teks->SQL, info schema)
from database_tools import text_to_sql, init_database, get_database_info

# --- 1. Page Configuration and Title ---
st.title("💬 Chatbot Analisa Iklan")
st.caption("Chatbot latihan untuk menganalisis data kampanye iklan menggunakan SQL (contoh latihan).")

# --- 2. Sidebar for Settings ---
with st.sidebar:
    st.subheader("Pengaturan")
    google_api_key = st.text_input("Kunci API Google AI", type="password")
    reset_button = st.button("Reset Percakapan", help="Bersihkan semua pesan dan mulai ulang")
    init_db_button = st.button("Inisialisasi Database Iklan", help="Buat dan isi database contoh data kampanye iklan")
    if init_db_button:
        with st.spinner("Menginisialisasi database..."):
            result = init_database()
            st.success(result)

# --- 3. API Key and Agent Initialization ---
if not google_api_key:
    st.info("Silakan masukkan kunci API Google AI di sidebar untuk mulai.", icon="🗝️")
    st.stop()

@tool
def execute_sql(sql_query: str):
    """
    Jalankan query SQL terhadap database kampanye iklan.
    Contoh query: "SELECT campaign_id, SUM(impressions) as impressions, SUM(clicks) as clicks FROM impressions GROUP BY campaign_id"
    """
    result = text_to_sql(sql_query)
    formatted_result = f"```sql\n{sql_query}\n```\n\nHasil Query:\n{result}"
    return formatted_result

@tool
def get_schema_info():
    """
    Mengembalikan skema tabel dan contoh data (baris pertama) untuk membantu membangun query SQL.
    Cocok untuk melihat tabel seperti: campaigns, ads, impressions, clicks, conversions, spend, channels, ds, dll.
    """
    return get_database_info()

# Buat agent baru bila belum ada atau bila API key berubah
if ("agent" not in st.session_state) or (getattr(st.session_state, "_last_key", None) != google_api_key):
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.2
        )

        # Prompt diarahkan ke analisa iklan: cek skema, buat SQL, jalankan, interpretasi metrik
        st.session_state.agent = create_react_agent(
            model=llm,
            tools=[get_schema_info, execute_sql],
            prompt="""You are an assistant that helps analyze advertising campaign data using SQL.

IMPORTANT: When a user asks about ad performance, follow these steps:
1. FIRST, call the get_schema_info tool to inspect table schemas and sample rows.
2. THEN, compose a proper SQLite SQL query that answers the user's question. Use JOINs and aliases when needed.
3. Execute the SQL using the execute_sql tool.
4. Interpret the numeric results and explain key metrics clearly (e.g., impressions, clicks, CTR, spend, CPC, conversions, CPA, ROAS).
5. Suggest short actionable insights or next steps based on results.

Guidelines:
- Use valid SQLite syntax.
- Aggregate metrics when appropriate (SUM, AVG, COUNT).
- Calculate derived metrics (CTR = clicks/impressions, CPC = spend/clicks, CPA = spend/conversions, ROAS = revenue/spend).
- Format SQL to be readable and include aliases.
- If query fails, explain the error, fix it, and retry.

This is a practice project. Do not ask the user to write SQL; generate queries yourself based on schema info."""
        )

        st.session_state._last_key = google_api_key
        st.session_state.pop("messages", None)
    except Exception as e:
        st.error(f"Invalid API Key or configuration error: {e}")
        st.stop()

# --- 4. Chat History Management ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if reset_button:
    st.session_state.pop("agent", None)
    st.session_state.pop("messages", None)
    st.rerun()

# --- 5. Display Past Messages ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. Handle User Input and Agent Communication ---
prompt = st.chat_input("Tanyakan tentang performa kampanye iklan, metrik, tren, atau rekomendasi...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        messages = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        with st.spinner("Memproses..."):
            response = st.session_state.agent.invoke({"messages": messages})

            if "messages" in response and len(response["messages"]) > 0:
                answer = response["messages"][-1].content

                sql_query = None
                for i, msg in enumerate(response["messages"]):
                    if hasattr(msg, "tool_call_id") and hasattr(msg, "name") and msg.name == "execute_sql":
                        if hasattr(msg, "content") and "```sql\n" in msg.content:
                            sql_parts = msg.content.split("```sql\n")
                            if len(sql_parts) > 1:
                                sql_query = sql_parts[1].split("\n```")[0].strip()
                                st.session_state.last_sql_query = sql_query
                    elif hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            if tool_call.get("name") == "execute_sql" and "sql_query" in tool_call.get("args", {}):
                                sql_query = tool_call["args"]["sql_query"]
                                st.session_state.last_sql_query = sql_query
            else:
                answer = "Maaf, saya tidak dapat menghasilkan respon."

    except Exception as e:
        answer = f"Terjadi kesalahan: {e}"

    with st.chat_message("assistant"):
        sql_query = None
        if hasattr(st.session_state, "last_sql_query"):
            sql_query = st.session_state.last_sql_query
            del st.session_state.last_sql_query

        if sql_query:
            st.code(sql_query, language="sql")

        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
