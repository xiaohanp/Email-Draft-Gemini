import os
import streamlit as st
import streamlit.components.v1 as components
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.core.zimbra_source import ZimbraSource
from src.core.gemini_drafter import GeminiDrafter
from src.core.models import Draft

st.set_page_config(page_title="Email AI Agent", page_icon="📧", layout="wide", initial_sidebar_state="collapsed")

# Inject custom CSS for a better aesthetic
st.markdown("""
<style>
    .email-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border-left: 5px solid #4a90e2;
        cursor: pointer;
    }
    .email-card:hover {
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        transform: translateY(-2px);
        transition: all 0.2s ease;
    }
    .email-subject {
        font-weight: 600;
        font-size: 1.1rem;
        color: #2c3e50;
    }
    .email-meta {
        font-size: 0.9rem;
        color: #7f8c8d;
        margin-bottom: 10px;
    }
    
    /* Remove the huge default Streamlit padding at the top of the page */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_thread' not in st.session_state:
    st.session_state.selected_thread = None
if 'current_draft' not in st.session_state:
    st.session_state.current_draft = ""
if 'active_source' not in st.session_state:
    st.session_state.active_source = None
if 'page' not in st.session_state:
    st.session_state.page = 0
if 'threads' not in st.session_state:
    with st.spinner("Auto-fetching from Inria Zimbra..."):
        try:
            source = ZimbraSource(
                host=os.getenv("INRIA_ZIMBRA_IMAP_HOST"),
                username=os.getenv("INRIA_ZIMBRA_EMAIL"),
                password=os.getenv("INRIA_ZIMBRA_PASSWORD"),
                email_address=os.getenv("INRIA_ZIMBRA_EMAIL"),
                name="Inria Zimbra"
            )
            st.session_state.active_source = source
            st.session_state.threads = source.get_recent_threads()
        except Exception as e:
            st.session_state.threads = []
            st.error(f"Error auto-fetching emails: {e}")

@st.cache_resource
def get_drafter():
    try:
        return GeminiDrafter()
    except Exception as e:
        st.error(f"Failed to initialize Gemini Drafter: {e}")
        return None

drafter = get_drafter()
my_persona = os.getenv("MY_PERSONA", "I am a helpful assistant.")

st.title("Email Drafting Assistant")

# Sidebar for controls
with st.sidebar:
    st.header("Settings & Sources")
    source_choice = st.radio("Select Email Source", ["Work Email", "Personal Email"])
    
    if st.button("Fetch Emails"):
        with st.spinner(f"Fetching from {source_choice}..."):
            try:
                if source_choice == "Work Email":
                    source = ZimbraSource(
                        host=os.getenv("WORK_IMAP_HOST"),
                        username=os.getenv("WORK_IMAP_EMAIL"),
                        password=os.getenv("WORK_IMAP_PASSWORD"),
                        email_address=os.getenv("WORK_IMAP_EMAIL"),
                        name="Work Email"
                    )
                else:
                    source = ZimbraSource(
                        host=os.getenv("PERSONAL_IMAP_HOST"),
                        username=os.getenv("PERSONAL_IMAP_USERNAME", os.getenv("PERSONAL_IMAP_EMAIL")),
                        password=os.getenv("PERSONAL_IMAP_PASSWORD"),
                        email_address=os.getenv("PERSONAL_IMAP_EMAIL"),
                        name="Personal Email"
                    )
                    
                st.session_state.active_source = source
                threads = source.get_recent_threads()
                st.session_state.threads = threads
                st.session_state.selected_thread = None
                st.session_state.current_draft = ""
                st.success(f"Fetched {len(threads)} recent threads.")
            except Exception as e:
                st.error(f"Error fetching emails: {e}")

# Main Layout
col1, col2, col3 = st.columns([1, 1.5, 1.5])

# Left Column: List of recent threads
with col1:
    st.subheader("Recent Threads")
    if 'threads' in st.session_state and st.session_state.threads:
        PAGE_SIZE = 10
        total_pages = max(1, (len(st.session_state.threads) - 1) // PAGE_SIZE + 1)
        
        start_idx = st.session_state.page * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE
        
        for idx, thread in enumerate(st.session_state.threads[start_idx:end_idx]):
            actual_idx = start_idx + idx
            latest = thread.latest_message
            if not latest:
                continue
                
            button_label = f"{latest.sender.split('<')[0].strip()}: {latest.subject[:40]}"
            if st.button(button_label, key=f"thread_{actual_idx}", use_container_width=True):
                st.session_state.selected_thread = thread
                st.session_state.current_draft = ""
                st.rerun()
                
        st.divider()
        pc1, pc2, pc3 = st.columns([1, 1, 1])
        with pc1:
            if st.button("◀ Prev", disabled=(st.session_state.page == 0), use_container_width=True):
                st.session_state.page -= 1
                st.rerun()
        with pc2:
            st.markdown(f"<div style='text-align: center; margin-top: 5px;'>{st.session_state.page + 1} / {total_pages}</div>", unsafe_allow_html=True)
        with pc3:
            if st.button("Next ▶", disabled=(st.session_state.page >= total_pages - 1), use_container_width=True):
                st.session_state.page += 1
                st.rerun()
    else:
        st.info("No threads fetched yet. Click 'Fetch Emails' in the sidebar.")

# Center Column: Detail View
with col2:
    if st.session_state.selected_thread:
        thread = st.session_state.selected_thread
        latest = thread.latest_message
        
        st.subheader(f"Subject: {latest.subject}")
        
        # Reverse the messages list so the newest reply is always at the top of the screen
        for msg in reversed(thread.messages):
            with st.container():
                st.markdown(f"**From:** {msg.sender}  \n**Date:** {msg.date.strftime('%b %d, %Y %H:%M')}  \n**Subject:** {msg.subject}")
                # Use a white background card for each individual email body to make them pop out against the off-white app background
                st.markdown(f"<div style='background-color: white; padding: 15px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 20px; white-space: pre-wrap; font-size: 0.95rem;'>{msg.body}</div>", unsafe_allow_html=True)

# Right Column: AI Draft and Edit
with col3:
    if st.session_state.selected_thread:
        thread = st.session_state.selected_thread
        latest = thread.latest_message
            
        st.divider()
        
        # Header and Language Switcher
        h_col1, h_col2 = st.columns([0.5, 0.5])
        with h_col1:
            st.subheader("AI Draft")
        with h_col2:
            target_language = st.radio("Language", ["English", "French"], horizontal=True, label_visibility="collapsed", key="draft_lang")
            
        if 'last_draft_lang' not in st.session_state:
            st.session_state.last_draft_lang = "English"

        # If language was changed while a draft exists, translate it
        if st.session_state.current_draft and st.session_state.last_draft_lang != st.session_state.draft_lang:
            with st.spinner(f"Translating draft to {st.session_state.draft_lang}..."):
                st.session_state.current_draft = drafter.refine_draft(
                    thread_context=thread.get_context(),
                    my_persona=my_persona,
                    current_draft=st.session_state.current_draft,
                    adjustment=f"Please translate this exact draft into {st.session_state.draft_lang}."
                )
                st.session_state.last_draft_lang = st.session_state.draft_lang
                st.rerun()
        
        if not st.session_state.current_draft and drafter:
            if st.button("Generate AI Draft"):
                with st.spinner("Generating draft with Gemini..."):
                    st.session_state.current_draft = drafter.draft_reply(thread.get_context(), my_persona, language=st.session_state.draft_lang)
                    st.session_state.last_draft_lang = st.session_state.draft_lang
                    st.rerun()
        
        if st.session_state.current_draft:
            if "[NEEDS_CONTEXT]" in st.session_state.current_draft:
                st.warning("Gemini indicated it doesn't have enough context to write a confident reply.")
                
            st.markdown("<br/>", unsafe_allow_html=True)
            
            # --- 1. Conversational Refinement Above the Editor ---
            if "refine_prompt_key" not in st.session_state:
                st.session_state.refine_prompt_key = 0

            refine_col1, refine_col2 = st.columns([0.8, 0.2])
            with refine_col1:
                prompt_input = st.text_input("Ask AI to adjust the draft (e.g. 'Make it more formal'):", 
                                             key=f"refine_input_{st.session_state.refine_prompt_key}")
            with refine_col2:
                # Add vertical margin so the button aligns nicely with the text input field
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                refine_btn = st.button("Adjust", use_container_width=True)

            if refine_btn and prompt_input:
                with st.spinner("Refining draft..."):
                    new_draft = drafter.refine_draft(
                        thread_context=thread.get_context(),
                        my_persona=my_persona,
                        current_draft=st.session_state.current_draft,
                        adjustment=prompt_input
                    )
                    st.session_state.current_draft = new_draft
                
                # Increment the key to force the text input to completely clear on reload
                st.session_state.refine_prompt_key += 1
                st.rerun()

            # --- 2. Copy Button Snug with the Editor Label ---
            draft_json = json.dumps(st.session_state.current_draft)
            copy_html = f"""
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600&display=swap');
                body {{ margin: 0; padding: 0; }}
                #copy-btn {{
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 400;
                    padding: 0.25rem 0.75rem;
                    border-radius: 0.5rem;
                    min-height: 38px;
                    margin: 0px;
                    line-height: 1.6;
                    color: rgb(49, 51, 63);
                    width: 100%;
                    user-select: none;
                    background-color: #FFFFFF;
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    cursor: pointer;
                    font-family: "Source Sans Pro", sans-serif;
                    font-size: 1rem;
                    transition: border-color 0.15s, color 0.15s;
                }}
                #copy-btn:hover {{
                    border-color: #1C83E1;
                    color: #1C83E1;
                }}
                #copy-btn:focus {{
                    outline: none;
                    border-color: #1C83E1;
                    color: #1C83E1;
                    box-shadow: rgba(28, 131, 225, 0.5) 0px 0px 0px 0.2rem;
                }}
            </style>
            <div>
                <button id="copy-btn">Copy</button>
            </div>
            <script>
                const btn = document.getElementById('copy-btn');
                btn.addEventListener('click', () => {{
                    const text = {draft_json};
                    if (navigator.clipboard && window.isSecureContext) {{
                        navigator.clipboard.writeText(text).then(() => {{
                            btn.innerText = 'Copied!'; setTimeout(() => btn.innerText = 'Copy', 2000);
                        }});
                    }} else {{
                        const ta = document.createElement('textarea');
                        ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
                        document.body.appendChild(ta); ta.select();
                        try {{ document.execCommand('copy'); btn.innerText = 'Copied!'; setTimeout(() => btn.innerText = 'Copy', 2000); }} 
                        catch (err) {{ btn.innerText = 'Failed'; }}
                        document.body.removeChild(ta);
                    }}
                }});
            </script>
            """
            
            # Place the label and the copy button on the same line to make it look like one box header
            col_label, col_btn = st.columns([0.8, 0.2])
            with col_label:
                st.markdown("**Review and Edit Draft:**")
            with col_btn:
                copy_btn_placeholder = st.empty()
            
            # The text area
            edited_draft = st.text_area("Review and Edit Draft:", value=st.session_state.current_draft, height=300, label_visibility="collapsed")
            st.session_state.current_draft = edited_draft
            
            # Inject updated text into copy button
            with copy_btn_placeholder:
                components.html(copy_html, height=42)
            
            if st.button("Save Draft to Inbox", use_container_width=True, type="primary"):
                if st.session_state.active_source:
                    draft = Draft(
                        thread_id=thread.id,
                        subject=f"Re: {latest.subject}",
                        body=st.session_state.current_draft,
                        to_address=latest.sender
                    )
                    success = st.session_state.active_source.save_draft(draft)
                    if success:
                        st.success("Draft saved successfully!")
                    else:
                        st.error("Failed to save draft.")
                else:
                    st.error("No active source selected.")
