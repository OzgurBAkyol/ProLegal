import streamlit as st


def section_header(title, description=None, help_text=None):
    st.header(title)
    if description:
        st.markdown(
            f"<div style='color: #555;'>{description}</div>", unsafe_allow_html=True
        )
    if help_text:
        with st.expander("Yardım / Açıklama"):
            st.info(help_text)


def show_error(msg):
    st.error(f"❌ {msg}")


def show_warning(msg):
    st.warning(f"⚠️ {msg}")


def show_success(msg):
    st.success(f"✅ {msg}")


def show_info(msg):
    st.info(msg)
