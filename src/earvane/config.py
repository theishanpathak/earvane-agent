from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file = ".env", extra="ignore")
    DATABASE_URL: str

    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str

    YOUTUBE_API_KEY: str

    GENIUS_ACCESS_TOKEN: str
    
    OPENAI_API_KEY: str

    #empty string for v1
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = ""

   
    

    ANTHROPIC_API_KEY: str = ""

settings = Settings()
