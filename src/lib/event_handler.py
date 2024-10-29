import streamlit as st


class StreamlitEventHandler:
    def __init__(self, text_boxes):
        self.text_boxes = text_boxes

    def update_tools_called(self, tools_called):
        self.text_boxes[-1] = st.expander("**💻 Code**", expanded=True)
        self.text_boxes[-1].info(f"**Tools Called:** {tools_called}")

    def update_tools_inputs(self, tools_inputs):
        self.text_boxes[-1].info(f"**Tools Inputs:** {tools_inputs}")

    def update_tools_outputs(self, tools_outputs):
        # Nest the code output in an expander
        self.text_boxes[-1] = st.expander(label="**🔎 Output**")
        # Clear the latest text box which is for the code output
        self.text_boxes[-1].empty()
        # Add the logs to the code output
        self.text_boxes[-1].info(
            f"**Tools Outputs:** {tools_outputs[0].get('output','')}"
        )

    def update_final_answer(self, answer, total_tokens):
        self.text_boxes[-1] = st.expander(label="**🕵️ Assistant** \n\n ")
        self.text_boxes[-1].info(f"{answer}")
        self.text_boxes[-1].info(f"**Total Tokens:** {total_tokens}")
