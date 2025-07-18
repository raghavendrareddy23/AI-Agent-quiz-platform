from typing import ClassVar, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    PORT: int = 8080
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    GROQ_API_KEY: str
    # GROQ_API_KEY_V2: str

    TOP_TECHNOLOGIES: ClassVar[List[str]] = [
        "Artificial Intelligence",
        "Machine Learning",
        "Deep Learning",
        "Natural Language Processing",
        "Computer Vision",
        "Generative AI",
        "Blockchain",
        "Web3",
        "Cryptocurrency",
        "Cloud Computing",
        "AWS",
        "Azure",
        "Google Cloud",
        "DevOps",
        "Docker",
        "Kubernetes",
        "Programming Languages",
        "Python",
        "JavaScript",
        "Java",
        "C++",
        "Web Development",
        "React",
        "Angular",
        "Vue.js",
        "Mobile Development",
        "Flutter",
        "React Native",
        "Data Science",
        "Big Data",
        "Hadoop",
        "Spark",
        "Cybersecurity",
        "Ethical Hacking",
        "Internet of Things",
        "Robotics",
        "Quantum Computing",
        "AR/VR",
    ]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
