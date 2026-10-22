import streamlit as st
import sqlite3
from datetime import datetime, date
from streamlit_mic_recorder import speech_to_text


# ==================================================
# PAGE SETTINGS
# ==================================================

st.set_page_config(
    page_title="MindVault AI",
    page_icon="🧠",
    layout="wide"
)


# ==================================================
# DATABASE CONNECTION
# ==================================================

conn = sqlite3.connect(
    "mindvault.db",
    check_same_thread=False
)

conn.row_factory = sqlite3.Row


# Create memories table
conn.execute("""
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
)
""")


# Create tasks table
conn.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    due_date TEXT,
    completed INTEGER DEFAULT 0
)
""")


# Add a voice-note identifier to existing databases.
# This also works if the column already exists.

memory_columns = {
    row["name"]
    for row in conn.execute(
        "PRAGMA table_info(memories)"
    ).fetchall()
}

if "is_voice_note" not in memory_columns:
    conn.execute("""
        ALTER TABLE memories
        ADD COLUMN is_voice_note INTEGER NOT NULL DEFAULT 0
    """)

conn.commit()


# ==================================================
# SAVE MEMORY
# ==================================================

def save_memory(title, category, content, is_voice_note=False):
    conn.execute("""
        INSERT INTO memories
        (title, category, content, created_at, is_voice_note)
        VALUES (?, ?, ?, ?, ?)
    """, (
        title,
        category,
        content,
        datetime.now().strftime("%d-%m-%Y %H:%M"),
        1 if is_voice_note else 0
    ))
    conn.commit()

# ==================================================
# GET MEMORIES
# ==================================================

def get_memories(search=""):

    search = f"%{search.strip()}%"

    return conn.execute("""
        SELECT * FROM memories
        WHERE title LIKE ?
           OR category LIKE ?
           OR content LIKE ?
        ORDER BY id DESC
    """, (
        search,
        search,
        search
    )).fetchall()


# ==================================================
# GET VOICE NOTES
# ==================================================

def get_voice_notes():

    return conn.execute("""
        SELECT * FROM memories
        WHERE is_voice_note = 1
        ORDER BY id DESC
    """).fetchall()


# ==================================================
# GET TASKS
# ==================================================

def get_tasks():

    return conn.execute("""
        SELECT * FROM tasks
        ORDER BY id DESC
    """).fetchall()


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

st.sidebar.title("🧠 MindVault AI")

st.sidebar.caption(
    "Your Intelligent Memory Companion"
)

pages = [
    "Dashboard",
    "My Memories",
    "AI Assistant",
    "Tasks & Planner",
    "Add New Memory",
    "Voice Notes"
]


# Handle dashboard navigation before creating the radio.
# This avoids modifying the radio widget's state
# after it has already been created.

if st.session_state.pop("go_to_voice_notes", False):
    st.session_state["navigation"] = "Voice Notes"


if "navigation" not in st.session_state:
    st.session_state["navigation"] = "Dashboard"


page = st.sidebar.radio(
    "Navigation",
    pages,
    key="navigation"
)


# ==================================================
# DASHBOARD
# ==================================================

if page == "Dashboard":

    st.title("✨ MindVault AI")

    st.subheader(
        "Your Intelligent Memory Companion"
    )

    st.write(
        "Save memories, organize tasks, "
        "and access important information."
    )

    memories = get_memories()
    tasks = get_tasks()
    voice_notes = get_voice_notes()

    # Dashboard metrics

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "🧠 Memories Saved",
        len(memories)
    )

    col2.metric(
        "📋 Total Tasks",
        len(tasks)
    )

    col3.metric(
        "🎙️ Voice Notes",
        len(voice_notes)
    )

    # Recent memories

    st.subheader(
        "🧠 Recent Memories"
    )

    if memories:

        for memory in memories[:5]:

            with st.container(border=True):

                st.markdown(
                    f"### {memory['title']}"
                )

                st.caption(
                    f"Category: {memory['category']} | "
                    f"Saved: {memory['created_at']}"
                )

                st.write(
                    memory["content"]
                )

    else:

        st.info(
            "No memories saved yet."
        )

    # Recent voice notes

    st.subheader(
        "🎙️ Recent Voice Notes"
    )

    if voice_notes:

        for note in voice_notes[:5]:

            with st.container(border=True):

                st.markdown(
                    f"### {note['title']}"
                )

                st.caption(
                    f"Saved: {note['created_at']}"
                )

                st.write(
                    note["content"]
                )

    else:

        st.info(
            "No voice notes saved yet."
        )

    # Navigation button is always visible

    if st.button(
        "🎙️ Go to Voice Notes",
        key="dashboard_voice_button"
    ):

        st.session_state["go_to_voice_notes"] = True
        st.rerun()

    # Today's focus

    st.subheader(
        "📅 Today's Focus"
    )

    pending = [
        task for task in tasks
        if not task["completed"]
    ]

    if pending:

        for task in pending:

            st.write(
                f"📝 {task['title']} — "
                f"{task['due_date'] or 'No due date'}"
            )

    else:

        st.success(
            "No pending tasks!"
        )


# ==================================================
# MY MEMORIES
# ==================================================

elif page == "My Memories":

    st.title(
        "🧠 My Memories"
    )

    search = st.text_input(
        "🔍 Search your memories"
    )

    memories = get_memories(search)

    if memories:

        for memory in memories:

            with st.container(border=True):

                st.subheader(
                    memory["title"]
                )

                st.caption(
                    f"Category: {memory['category']} | "
                    f"Saved: {memory['created_at']}"
                )

                st.write(
                    memory["content"]
                )

                if st.button(
                    "🗑️ Delete",
                    key=f"delete_memory_{memory['id']}"
                ):

                    conn.execute(
                        "DELETE FROM memories WHERE id = ?",
                        (memory["id"],)
                    )

                    conn.commit()
                    st.rerun()

    else:

        st.info(
            "No matching memories found."
        )


# ==================================================
# ADD NEW MEMORY
# ==================================================

elif page == "Add New Memory":

    st.title(
        "➕ Add New Memory"
    )

    with st.form(
        "memory_form",
        clear_on_submit=True
    ):

        title = st.text_input(
            "Memory title"
        )

        category = st.selectbox(
            "Category",
            [
                "Study",
                "Personal",
                "Work",
                "Ideas",
                "Other"
            ]
        )

        content = st.text_area(
            "Memory details"
        )

        submitted = st.form_submit_button(
            "💾 Save Memory"
        )

        if submitted:

            if title.strip() and content.strip():

                save_memory(
                    title.strip(),
                    category,
                    content.strip()
                )

                st.success(
                    "Memory saved successfully!"
                )

            else:

                st.error(
                    "Enter both a title and memory details."
                )


# ==================================================
# AI ASSISTANT
# ==================================================

elif page == "AI Assistant":

    st.title(
        "🤖 AI Assistant"
    )

    st.write(
        "Search for information in your saved memories."
    )

    st.info(
        "This version uses keyword search. "
        "A generative AI model is not connected yet."
    )

    question = st.text_input(
        "What would you like to find?",
        placeholder="Example: Python learning plan"
    )

    if st.button(
        "🔎 Search My Memories"
    ):

        if question.strip():

            results = get_memories(question)

            if results:

                for memory in results:

                    with st.container(border=True):

                        st.subheader(
                            memory["title"]
                        )

                        st.caption(
                            memory["category"]
                        )

                        st.write(
                            memory["content"]
                        )

            else:

                st.warning(
                    "No matching memories found."
                )

        else:

            st.warning(
                "Please enter a search term."
            )


# ==================================================
# TASKS & PLANNER
# ==================================================

elif page == "Tasks & Planner":

    st.title(
        "📅 Tasks & Planner"
    )

    with st.form(
        "task_form",
        clear_on_submit=True
    ):

        title = st.text_input(
            "Task name"
        )

        due_date = st.date_input(
            "Due date",
            value=date.today()
        )

        submitted = st.form_submit_button(
            "➕ Add Task"
        )

        if submitted:

            if title.strip():

                conn.execute("""
                    INSERT INTO tasks
                    (title, due_date)
                    VALUES (?, ?)
                """, (
                    title.strip(),
                    due_date.isoformat()
                ))

                conn.commit()

                st.success(
                    "Task added successfully!"
                )

                st.rerun()

            else:

                st.error(
                    "Enter a task name."
                )

    st.subheader(
        "Your Tasks"
    )

    tasks = get_tasks()

    if tasks:

        for task in tasks:

            col1, col2 = st.columns([4, 1])

            with col1:

                status = (
                    "✅"
                    if task["completed"]
                    else "⬜"
                )

                st.write(
                    f"{status} **{task['title']}**"
                )

                st.caption(
                    f"Due date: "
                    f"{task['due_date'] or 'Not set'}"
                )

            with col2:

                if not task["completed"]:

                    if st.button(
                        "Complete",
                        key=f"complete_{task['id']}"
                    ):

                        conn.execute("""
                            UPDATE tasks
                            SET completed = 1
                            WHERE id = ?
                        """, (task["id"],))

                        conn.commit()
                        st.rerun()

                if st.button(
                    "🗑️",
                    key=f"delete_task_{task['id']}"
                ):

                    conn.execute(
                        "DELETE FROM tasks WHERE id = ?",
                        (task["id"],)
                    )

                    conn.commit()
                    st.rerun()

    else:

        st.info(
            "No tasks yet. Add your first task above."
        )


# ==================================================
# VOICE NOTES
# ==================================================

elif page == "Voice Notes":

    st.title(
        "🎙️ Voice Notes"
    )

    st.write(
        "Record your thoughts and save them as memories."
    )

    # Voice recording component

    voice_text = speech_to_text(
        language="en",
        start_prompt="🎤 Start Recording",
        stop_prompt="⏹️ Stop Recording",
        just_once=True,
        key="mindvault_voice"
    )

    if voice_text:

        st.subheader(
            "Your Voice Note"
        )

        with st.form(
            "voice_note_form",
            clear_on_submit=True
        ):

            title = st.text_input(
                "Memory title",
                value="My Voice Note"
            )

            category = st.selectbox(
                "Category",
                [
                    "Personal",
                    "Study",
                    "Work",
                    "Ideas",
                    "Other"
                ]
            )

            st.text_area(
                "Converted text",
                value=voice_text,
                height=150,
                disabled=True
            )

            submitted = st.form_submit_button(
                "💾 Save Voice Note"
            )

            if submitted:

                if title.strip() and voice_text.strip():

                    save_memory(
                        title=title.strip(),
                        category=category,
                        content=voice_text.strip(),
                        is_voice_note=True
                    )

                    st.success(
                        "Voice note saved successfully!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Please enter a title and record your voice."
                    )

    else:

        st.info(
            "Click Start Recording, allow microphone access, "
            "speak clearly, and then stop recording."
        )

    # ----------------------------------------------
    # VOICE NOTES HISTORY
    # ----------------------------------------------

    st.divider()

    st.subheader(
        "📚 Voice Notes History"
    )

    voice_notes = get_voice_notes()

    if voice_notes:

        for note in voice_notes:

            with st.container(border=True):

                st.markdown(
                    f"### 🎙️ {note['title']}"
                )

                st.caption(
                    f"Category: {note['category']} | "
                    f"Saved: {note['created_at']}"
                )

                st.write(
                    note["content"]
                )

                if st.button(
                    "🗑️ Delete Voice Note",
                    key=f"delete_voice_{note['id']}"
                ):

                    conn.execute(
                        "DELETE FROM memories WHERE id = ?",
                        (note["id"],)
                    )

                    conn.commit()
                    st.rerun()

    else:

        st.info(
            "No voice notes saved yet. "
            "Record and save your first voice note above."
        )


# ==================================================
# CLOSE DATABASE CONNECTION
# ==================================================

# Streamlit reruns the script frequently, so the
# connection is left open during normal page rendering.