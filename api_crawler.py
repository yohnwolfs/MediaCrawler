# 声明：本代码仅供学习和研究目的使用。
# 详细许可条款请参阅项目根目录下的LICENSE文件。

import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import config
from media_platform.xhs.core import XiaoHongShuCrawler
from playwright.async_api import async_playwright
import traceback

app = FastAPI()

class XhsDetailRequest(BaseModel):
    note_url_list: List[str]
    cookies: Optional[str] = None  # 可选，支持自定义 cookie

class XhsCommentsRequest(BaseModel):
    note_ids: List[str]  # 笔记ID列表
    xsec_tokens: List[str]  # 对应的xsec_token列表
    cookies: Optional[str] = None  # 可选，支持自定义 cookie
    max_comments_count: Optional[int] = 10  # 可选，每个笔记最大评论数量
    enable_get_sub_comments: Optional[bool] = False  # 可选，是否获取子评论

@app.get("/")
async def test():
    return 'api working!'

@app.post("/xhs_detail")
async def xhs_detail_api(req: XhsDetailRequest):

    # 动态设置 config
    if req.cookies:
        config.COOKIES = req.cookies
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
        traceback.print_exc()
        await crawler.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/xhs_comments")
async def xhs_comments_api(req: XhsCommentsRequest):
    if len(req.note_ids) != len(req.xsec_tokens):
        raise HTTPException(status_code=400, detail="笔记ID列表和xsec_token列表长度必须相同")
        
    # 动态设置 config
    if req.cookies:
        config.COOKIES = req.cookies
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
        traceback.print_exc()
        await crawler.close()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("api_crawler:app", host="0.0.0.0", port=8712, reload=True) 