from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 初始化FastAPI应用
app = FastAPI(
    title="LangChain API 服务",
    description="提供基于LangChain的AI能力接口",
    version="1.0.0",
    contact={
        "name": "技术支持",
        "email": "support@example.com"
    }
)

add_routes(
    app,
    ChatOpenAI(
        model="deepseek/deepseek-chat-v3-0324:free",
        openai_api_key="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",
        openai_api_base="https://openrouter.ai/api/v1",
    ),
    path="/openai",
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个喜欢写故事的助手,每次只写100字左右"),
        ("user", "写一个故事，主题是: {topic}")
    ]
)
add_routes(
    app,
    prompt | ChatOpenAI(
        model="deepseek/deepseek-chat-v3-0324:free",
        openai_api_key="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",
        openai_api_base="https://openrouter.ai/api/v1",
    ),
    path="/openai_ext",
)





















# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 首页重定向到文档
@app.get("/", include_in_schema=False)
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
