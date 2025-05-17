# 声明：本代码仅供学习和研究目的使用。
# 详细许可条款请参阅项目根目录下的LICENSE文件。

import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import config
from media_platform.xhs.core import XiaoHongShuCrawler
from playwright.async_api import async_playwright
import traceback

app = FastAPI()

class XhsDetailRequest(BaseModel):
    note_url_list: List[str]

class XhsCommentsRequest(BaseModel):
    note_ids: List[str]  # 笔记ID列表
    xsec_tokens: List[str]  # 对应的xsec_token列表
    max_comments_count: Optional[int] = 10  # 可选，每个笔记最大评论数量
    enable_get_sub_comments: Optional[bool] = False  # 可选，是否获取子评论

class XhsSearchRequest(BaseModel):
    keywords: str  # 搜索关键词，多个关键词用逗号分隔
    sort_type: Optional[str] = None  # 可选，排序方式
    max_notes_count: Optional[int] = None  # 可选，最大帖子数

@app.get("/")
async def test():
    return 'api working!'

@app.post("/xhs_detail")
async def xhs_detail_api(req: XhsDetailRequest, request: Request):
    # 从请求头获取 cookies
    cookies = request.headers.get("cookie")
    if cookies:
        config.COOKIES = cookies
    config.CRAWLER_TYPE = "detail"
    config.PLATFORM = "xhs"
    config.XHS_SPECIFIED_NOTE_URL_LIST = req.note_url_list
    # 关闭保存到文件，仅返回数据
    config.SAVE_DATA_OPTION = "json"

    crawler = XiaoHongShuCrawler()
    try:
        async with async_playwright() as playwright:

            # 初始化爬虫
            await crawler.setup_playwright(playwright)
            # 只爬取并返回数据
            result = await crawler.get_specified_notes_and_return(note_url_list=req.note_url_list)
            # 确保在获取完所有数据后再关闭浏览器
            await crawler.close()

            return {"status": "ok", "data": result}

    except Exception as e:
        if hasattr(e, "last_attempt") and "登录已过期" in str(e.last_attempt.exception()):
            return {"status": "error", "message": "登录已过期"}
        traceback.print_exc()
        await crawler.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/xhs_comments")
async def xhs_comments_api(req: XhsCommentsRequest, request: Request):
    if len(req.note_ids) != len(req.xsec_tokens):
        raise HTTPException(status_code=400, detail="笔记ID列表和xsec_token列表长度必须相同")
        
    # 从请求头获取 cookies
    cookies = request.headers.get("cookie")
    if cookies:
        config.COOKIES = cookies
    config.CRAWLER_TYPE = "detail"
    config.PLATFORM = "xhs"
    # 关闭保存到文件，仅返回数据
    config.SAVE_DATA_OPTION = "json"
    # 设置评论数量限制
    if req.max_comments_count:
        config.CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = req.max_comments_count
    # 设置是否获取子评论
    if req.enable_get_sub_comments is not None:
        config.ENABLE_GET_SUB_COMMENTS = req.enable_get_sub_comments

    crawler = XiaoHongShuCrawler()
    try:

        async with async_playwright() as playwright:

            # 初始化爬虫
            await crawler.setup_playwright(playwright)

            results = await crawler.batch_get_note_comments_and_return(req.note_ids, req.xsec_tokens)

            await crawler.close()

            return {"status": "ok", "data": results}
  
    except Exception as e:
        if hasattr(e, "last_attempt") and "登录已过期" in str(e.last_attempt.exception()):
            return {"status": "error", "message": "登录已过期"}
        traceback.print_exc()
        await crawler.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/xhs_search")
async def xhs_search_api(req: XhsSearchRequest, request: Request):
    # 从请求头获取 cookies
    cookies = request.headers.get("cookie")
    if cookies:
        config.COOKIES = cookies
    config.CRAWLER_TYPE = "search"
    config.PLATFORM = "xhs"
    # 排序方式
    if req.sort_type:
        config.SORT_TYPE = req.sort_type
    # 最大帖子数
    if req.max_notes_count:
        config.CRAWLER_MAX_NOTES_COUNT = req.max_notes_count
    # 关闭保存到文件，仅返回数据
    config.SAVE_DATA_OPTION = "json"

    crawler = XiaoHongShuCrawler()
    try:
        async with async_playwright() as playwright:
            # 初始化爬虫
            await crawler.setup_playwright(playwright)
            # 搜索并返回数据
            result = await crawler.search_and_return(keywords=req.keywords, enable_comments=True)
            await crawler.close()
            return {"status": "ok", "data": result}
    except Exception as e:
        if hasattr(e, "last_attempt") and "登录已过期" in str(e.last_attempt.exception()):
            return {"status": "error", "message": "登录已过期"}
        traceback.print_exc()
        await crawler.close()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("api_crawler:app", host="0.0.0.0", port=8712, reload=True) 