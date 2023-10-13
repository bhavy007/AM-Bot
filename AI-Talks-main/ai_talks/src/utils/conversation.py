from random import randrange

import streamlit as st
from openai.error import InvalidRequestError, OpenAIError
from streamlit_chat import message

from .agi.chat_gpt import create_gpt_completion
from .stt import show_voice_input
from .tts import show_audio_player

chat_prompt = """
# I trying to automate the interview conducting process. I want you to act as an interviewer from Bharti Airtel (name: Shahrukh), where I will provide you with job description and an interview flow. The candidate is supposed to answer them in real-time, and you will ask further questions based on their responses. The candidate has already shown some interest by applying on a career website to this job.
# For now imagine the candidate will be giving you responses in this chat only. Ask the questions one by one.

# Remember the following things - 
# - DO NOT ANSWER ANY queries by the candidate which are not related the interview. Simply ignore them by sticking to questions related to the interview.

# - Once the entire interview is conducted, make a detailed report of the answers given. Compile the questions and answers in a format so that they can be put into an excel sheet.

# This is the Job description - 
# The responsibility of the role holder is to ensure sales and service in his territory to deliver Data (Internet Bandwidth, MPLS, Cloud etc. ), Voice (Postpaid), Broadband and Fixed Line Business in the assigned territory. Front-end the relationship with customer from Airtel side and become the single point of contact for customer for all three lines of business. Ensure Customer Market Share (CMS) and Revenue Market Share (RMS) growth in both existing and new accounts.

# Responsibilities:
# Role - Account Manager Role
# Deliver Data, Voice and Fixed Line installation as per assigned targets
# New account break-in (hunting) for Data, Voice and Fixed Line.
# Cross-sell multi-product lines in existing and new customer
# Build & maintain healthy funnel for all three Lines of Business with earmarked levels of maturity
# Be aware of competition plans & collect insights for market intelligence
# Monitor competition's customer offerings and planning sales interventions for different class of clients.
# Build and maintain strong, long lasting client relationships
# Negotiate and close orders/contracts to maximize revenue
# Develop new business through upsell and cross-sell with existing clients
# Ensure timely and successful delivery of our solutions as per client needs

# Here is the Interview Flow - 

# I. Greeting Candidates:
# • Begin the interview with a warm welcome and introductions.

# II. Resume Source:
# • Mention the source of the candidate's resume eg Naukri.com etc

# III. Job Title Explanation:
# • Provide a brief overview of the job title and its key responsibilities.

# IV. Tell Us About Yourself:
# • Invite the candidate to introduce themselves, focusing on their background, work experience and education.

# V. Work Experience and Position-Related Questions:
# • Dive into their work experience by asking specific questions related to their previous roles, accomplishments, and relevant skills.

# VI. Detailed Job Opening Explanation:
# • Provide a comprehensive description of the job opening at Airtel, including the type of work involved and its significance within the organization.
# • Ask the candidate about their interest in and qualifications for the position.

# VII. Current and Expected CTC:
# • Inquire about their current and expected CTC, including details on fixed and variable components.

# VIII. Location Preference:
# • Discuss the candidate's preferred work location and whether they are open to relocation if necessary.

# IX. Notice Period:
# • Ask about their notice period in their current company to understand their availability for joining Airtel.

# X. Reason for Switching Companies:
# • If applicable, inquire about the candidate's motivation for leaving their current job and seeking a new opportunity.

# XI. Further Steps:
# • Explain the next steps in the interview process, - AMCAT test and subsequent interview rounds.
# • Provide information on the timeline for these steps and any other relevant details

# Start the interview once I type "Begin Interview"
"""

def clear_chat() -> None:
    st.session_state.generated = []
    st.session_state.past = []
    st.session_state.messages = []
    st.session_state.user_text = ""
    st.session_state.seed = randrange(10**8)  # noqa: S311
    st.session_state.costs = []
    st.session_state.total_tokens = []


def show_text_input() -> None:
    st.text_area(label=st.session_state.locale.chat_placeholder, value=st.session_state.user_text, key="user_text")


def get_user_input():
    match st.session_state.input_kind:
        case st.session_state.locale.input_kind_1:
            show_text_input()
        case st.session_state.locale.input_kind_2:
            show_voice_input()
        case _:
            show_text_input()


def show_chat_buttons() -> None:
    b0, b1, b2 = st.columns(3)
    with b0, b1, b2:
        b0.button(label=st.session_state.locale.chat_run_btn)
        b1.button(label=st.session_state.locale.chat_clear_btn, on_click=clear_chat)
        b2.download_button(
            label=st.session_state.locale.chat_save_btn,
            data="\n".join([str(d) for d in st.session_state.messages[1:]]),
            file_name="ai-talks-chat.json",
            mime="application/json",
        )


def show_chat(ai_content: str, user_text: str) -> None:
    if ai_content not in st.session_state.generated:
        # store the ai content
        st.session_state.past.append(user_text)
        st.session_state.generated.append(ai_content)
    if st.session_state.generated:
        for i in range(len(st.session_state.generated)):
            message(st.session_state.past[i], is_user=True, key=str(i) + "_user", seed=st.session_state.seed)
            message("", key=str(i), seed=st.session_state.seed)
            st.markdown(st.session_state.generated[i])
            st.caption(f"""
                {st.session_state.locale.tokens_count}{st.session_state.total_tokens[i]} |
                {st.session_state.locale.message_cost}{st.session_state.costs[i]:.5f}$
            """, help=f"{st.session_state.locale.total_cost}{sum(st.session_state.costs):.5f}$")


def calc_cost(usage: dict) -> None:
    total_tokens = usage.get("total_tokens")
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    st.session_state.total_tokens.append(total_tokens)
    # pricing logic: https://openai.com/pricing#language-models
    if st.session_state.model == "gpt-3.5-turbo":
        cost = total_tokens * 0.002 / 1000
    else:
        cost = (prompt_tokens * 0.03 + completion_tokens * 0.06) / 1000
    st.session_state.costs.append(cost)


def show_gpt_conversation() -> None:
    try:
        completion = create_gpt_completion(st.session_state.model, st.session_state.messages)
        ai_content = completion.get("choices")[0].get("message").get("content")
        calc_cost(completion.get("usage"))
        st.session_state.messages.append({"role": "assistant", "content": ai_content})
        if ai_content:
            show_chat(ai_content, st.session_state.user_text)
            st.divider()
            show_audio_player(ai_content)
    except InvalidRequestError as err:
        if err.code == "context_length_exceeded":
            st.session_state.messages.pop(1)
            if len(st.session_state.messages) == 1:
                st.session_state.user_text = ""
            show_conversation()
        else:
            st.error(err)
    except (OpenAIError, UnboundLocalError) as err:
        st.error(err)


def show_conversation() -> None:
    if st.session_state.messages:
        st.session_state.messages.append({"role": "user", "content": st.session_state.user_text})
    else:
        ai_role = f"{st.session_state.locale.ai_role_prefix} {st.session_state.role}. {st.session_state.locale.ai_role_postfix}"  # NOQA: E501
        st.session_state.messages = [
            {"role": "system", "content": chat_prompt},
            {"role": "user", "content": st.session_state.user_text},
        ]
    show_gpt_conversation()
