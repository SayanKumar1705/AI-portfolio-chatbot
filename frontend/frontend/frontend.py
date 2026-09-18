"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
import httpx

from rxconfig import config


class State(rx.State):
    """The app state."""
    question: str = ""
    messages: list[str] = []

    def set_question_text(self, value: str):
        self.question = value

    async def send_message(self):
        user_question = self.question
        self.messages.append(f"You: {user_question}")
        self.question = ""
        self.messages.append("AI: ")
        yield rx.call_script(
            "document.getElementById('chat-box').scrollTop = document.getElementById('chat-box').scrollHeight"
        )

        buffer = ""
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "http://127.0.0.1:8080/chat",
                json={"question": user_question},
            ) as response:
                async for chunk in response.aiter_text():
                    buffer += chunk
                    if len(buffer) > 5:
                        self.messages[-1] += buffer
                        buffer = ""
                        yield rx.call_script(
                            "document.getElementById('chat-box').scrollTop = document.getElementById('chat-box').scrollHeight"
                        )
        if buffer:
            self.messages[-1] += buffer
            yield rx.call_script(
                "document.getElementById('chat-box').scrollTop = document.getElementById('chat-box').scrollHeight"
            )

    def clear_chat(self):
        self.messages = []


def message_bubble(msg: str) -> rx.Component:
    is_user = msg.startswith("You:")
    return rx.box(
        rx.markdown(msg.replace("You: ", "").replace("AI: ", "")),
        background=rx.cond(
            is_user,
            "linear-gradient(135deg, #7928CA, #FF0080)",
            "#1a1a24",
        ),
        color="white",
        padding="14px 18px",
        border_radius="18px",
        max_width="70%",
        margin_left=rx.cond(is_user, "auto", "0"),
        margin_right=rx.cond(is_user, "0", "auto"),
        margin_bottom="12px",
        box_shadow="0 4px 12px rgba(0,0,0,0.3)",
        animation="fadeIn 0.4s ease-out",
    )


def index() -> rx.Component:
    return rx.box(
        rx.container(
            rx.vstack(
                rx.vstack(
                    rx.heading(
                        "Sayan's AI Portfolio",
                        size="9",
                        background_image="linear-gradient(to right, #7928CA, #FF0080, #7928CA)",
                        background_clip="text",
                        color="transparent",
                        font_weight="bold",
                    ),
                    rx.text(
                        "Ask me anything about my skills and experience",
                        color="#9999aa",
                        font_size="16px",
                    ),
                    spacing="1",
                    align="center",
                    width="100%",
                    text_align="center",
                    animation="titleFadeIn 1.2s ease-out",
                ),

                rx.box(
                    rx.foreach(State.messages, message_bubble),
                    id="chat-box",
                    height="550px",
                    width="100%",
                    overflow_y="auto",
                    padding="24px",
                    border_radius="20px",
                    background="rgba(255,255,255,0.03)",
                    border="1px solid rgba(255,255,255,0.08)",
                    backdrop_filter="blur(10px)",
                ),

                rx.hstack(
                    rx.input(
                        placeholder="Type your question...",
                        value=State.question,
                        on_change=State.set_question_text,
                        background="rgba(255,255,255,0.06)",
                        color="white",
                        border="1px solid rgba(255,255,255,0.1)",
                        border_radius="14px",
                        font_size="16px",
                        line_height="52px",
                        height="52px",
                        padding="0px 18px",
                        flex="1",
                        transition="border 0.2s ease",
                        _focus={"border": "1px solid #7928CA"},
                    ),
                    rx.button(
                        "Send",
                        on_click=State.send_message,
                        background="linear-gradient(135deg, #7928CA, #FF0080)",
                        color="white",
                        border_radius="14px",
                        padding="14px 26px",
                        font_weight="bold",
                        box_shadow="0 4px 14px rgba(121,40,202,0.4)",
                        transition="transform 0.2s ease, box-shadow 0.2s ease",
                        _hover={"transform": "scale(1.05)", "box_shadow": "0 6px 20px rgba(121,40,202,0.6)"},
                    ),
                    rx.button(
                        "Clear",
                        on_click=State.clear_chat,
                        background="rgba(255,255,255,0.06)",
                        color="#ccc",
                        border="1px solid rgba(255,255,255,0.1)",
                        border_radius="14px",
                        padding="14px 20px",
                        transition="background 0.2s ease",
                        _hover={"background": "rgba(255,255,255,0.12)"},
                    ),
                    width="100%",
                    spacing="3",
                ),

                spacing="6",
                width="100%",
                max_width="800px",
            ),
            padding_y="60px",
        ),
        background="radial-gradient(circle at top, #1a1030 0%, #0a0a0f 60%)",
        min_height="100vh",
        width="100%",
    )


style = {
    "@keyframes fadeIn": {
        "from": {"opacity": "0", "transform": "translateY(10px)"},
        "to": {"opacity": "1", "transform": "translateY(0)"},
    },
    "@keyframes titleFadeIn": {
        "from": {"opacity": "0", "transform": "translateY(-20px)"},
        "to": {"opacity": "1", "transform": "translateY(0)"},
    },
}

app = rx.App(style=style)
app.add_page(index)