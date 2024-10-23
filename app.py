import streamlit as st
from typing import Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from typing import List, Type, Any
import os
from typing import Optional, Any

class LLMConfig:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o-mini",
        max_tokens: int = 1500,
        temperature: float = 0.7,
        custom_model: Optional[Any] = None,
        base_url: Optional[str] = None,
        default_headers: Optional[dict] = None
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.custom_model = custom_model
        self.base_url = base_url
        self.default_headers = default_headers

class Flashcard(BaseModel):
    front: str = Field(..., description="The front side of the flashcard with a question or key term")
    back: str = Field(..., description="The back side of the flashcard with the answer or definition")
    explanation: Optional[str] = Field(None, description="An optional explanation or additional context")

class FlashcardSet(BaseModel):
    title: str = Field(..., description="The title or topic of the flashcard set")
    flashcards: List[Flashcard] = Field(..., description="A list of flashcards in this set")
class ContentEngine:
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        if llm_config is None:
            llm_config = LLMConfig()
        self.llm = self._initialize_llm(llm_config)

    def _initialize_llm(self, llm_config: LLMConfig):
        if llm_config.custom_model:
            return llm_config.custom_model
        else:
            return ChatOpenAI(
                model=llm_config.model_name,
                api_key=llm_config.api_key,
                max_tokens=llm_config.max_tokens,
                temperature=llm_config.temperature,
                base_url=llm_config.base_url,
                default_headers=llm_config.default_headers
            )
    
    def generate_flashcards(
        self,
        topic: str,
        num: int = 10,
        prompt_template: Optional[str] = None,
        custom_instructions: Optional[str] = None,
        response_model: Optional[Type[Any]] = None,
        llm: Optional[Any] = None,
        **kwargs
    ) -> FlashcardSet:
        if response_model is None:
            response_model = FlashcardSet
        parser = PydanticOutputParser(pydantic_object=response_model)
        format_instructions = parser.get_format_instructions()

        if prompt_template is None:
            prompt_template = """
            Generate a set of {num} flashcards on the topic: {topic}.

            For each flashcard, provide:
            1. A front side with a question or key term
            2. A back side with the answer or definition
            3. An optional explanation or additional context

            The flashcards should cover key concepts, terminology, and important facts related to the topic.

            Ensure that the output follows this structure:
            - A title for the flashcard set (the main topic)
            - A list of flashcards, each containing:
              - front: The question or key term
              - back: The answer or definition
              - explanation: Additional context or explanation (optional)
            """

        if custom_instructions:
            prompt_template += f"\n\nAdditional Instructions:\n{custom_instructions}"

        prompt_template += "\n\nThe response should be in JSON format.\n{format_instructions}"

        flashcard_prompt = PromptTemplate(
            input_variables=["num", "topic"],
            template=prompt_template,
            partial_variables={"format_instructions": format_instructions}
        )

        llm_to_use = llm if llm is not None else self.llm
        flashcard_chain = flashcard_prompt | llm_to_use
        results = flashcard_chain.invoke(
            {"num": num, "topic": topic, **kwargs},
        )

        try:
            structured_output = parser.parse(results.content)
            return structured_output
        except Exception as e:
            print(f"Error parsing output: {e}")
            print("Raw output:")
            print(results.content)
            return FlashcardSet(title=topic, flashcards=[])

# Initialize ContentEngine
llm_config = LLMConfig(api_key=st.secrets["OPENAI_API_KEY"])
content_engine = ContentEngine(llm_config)

st.set_page_config(page_title="EduChain Flashcard Generator", page_icon="📚")

st.title("📚 educhain Flashcard Generator")

# Add a brief description
st.markdown("""
Generate custom flashcards on any topic using AI! Perfect for studying and quick learning.
""")

# User input with improved styling
col1, col2 = st.columns([3, 1])
with col1:
    topic = st.text_input("📝 Enter the topic for flashcards:", placeholder="e.g., Python Programming")
with col2:
    num_cards = st.number_input("🔢 Number of cards:", min_value=1, max_value=20, value=5)

if st.button("🚀 Generate Flashcards"):
    if topic:
        with st.spinner("🧠 Generating flashcards..."):
            flashcard_set = content_engine.generate_flashcards(topic, num=num_cards)
        
        st.success(f"✅ Generated {len(flashcard_set.flashcards)} flashcards for '{flashcard_set.title}'")
        
        # Display flashcards with improved styling
        for i, flashcard in enumerate(flashcard_set.flashcards, 1):
            with st.expander(f"Flashcard {i}: {flashcard.front}"):
                st.markdown(f"**Back:** {flashcard.back}")
                if flashcard.explanation:
                    st.markdown(f"**Explanation:** {flashcard.explanation}")
    else:
        st.warning("⚠️ Please enter a topic for the flashcards.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #888;">
        Made with ❤️ by <a href="https://github.com/satvik314/educhain" target="_blank">EduChain</a> | Powered by AI
    </div>
    """,
    unsafe_allow_html=True
)

# CSS to style the flashcards and overall app
st.markdown("""
<style>
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
    h1 {
        color: #4a4a4a;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
    }
    .stExpander {
        background-color: #f0f0f0;
        border-radius: 10px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stExpander > div:first-child {
        background-color: #e0e0e0;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        padding: 10px;
        font-weight: bold;
        color: #333;
    }
    .stExpander > div:last-child {
        padding: 15px;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    .stNumberInput>div>div>input {
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)
