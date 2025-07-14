from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import List

from app.services.ai_agent_service import AIAgentService
from app.models.user import User
from app.utils.dependencies import get_current_user 

router = APIRouter()
ai_service = AIAgentService()


@router.get("/recommendations", summary="Get recommended quizzes for the current user")
async def get_recommendations(
    current_user: User = Depends(get_current_user), 
):
    try:
        recommendations = await ai_service.get_recommendations(user_id=current_user.id)
        return {"success": True, "data": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending", summary="Get top trending technologies")
async def get_trending_technologies():
    try:
        from app.models.database import get_db
        from app.models.quiz import QuizTrend

        db = next(get_db())
        trending = (
            db.query(QuizTrend)
            .order_by(QuizTrend.popularity_score.desc())
            .limit(5)
            .all()
        )
        return {
            "success": True,
            "data": [
                {"technology": trend.technology, "score": trend.popularity_score}
                for trend in trending
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading trends: {str(e)}")


@router.get("/leaderboard", summary="Get top users by total quiz score")
async def get_leaderboard():
    try:
        leaderboard = await ai_service.get_leaderboard()
        return {"success": True, "data": leaderboard}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting leaderboard: {str(e)}"
        )
