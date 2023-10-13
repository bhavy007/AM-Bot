from pathlib import Path

import streamlit as st

from .constants import BUG_REPORT_URL, REPO_URL
from .helpers import render_svg


def show_info(icon: Path) -> None:
    st.divider()
    st.markdown(f"<div style='text-align: justify;'>{st.session_state.locale.responsibility_denial}</div>",
                unsafe_allow_html=True)
    st.divider()
    st.markdown(f"""
        ### :page_with_curl: {st.session_state.locale.footer_title}
        - {render_svg(icon)} [{st.session_state.locale.footer_chat}](https://t.me/9958946215)
       
    """, unsafe_allow_html=True)
    st.divider()
    


def show_donates() -> None:
    st.markdown(f"""""")
    _, img_col, _ = st.columns(3)
    with img_col:
        st.image("ai_talks/assets/qr/tink.png", width=200)
    st.divider()
    st.markdown(f"<div style='text-align: justify;'>{st.session_state.locale.donates_info}</div>",
                unsafe_allow_html=True)
