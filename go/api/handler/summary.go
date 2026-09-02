package handler

// go/api/handler/summary.go

import (
	"errors"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	service "github.com/jishnu70/Youtube_video_summarizer/internal/service"
)

type SummaryHandler struct {
	videoSummaryService *service.VideoSummaryService
}

func NewSummaryHandler(videoSummaryService *service.VideoSummaryService) *SummaryHandler {
	return &SummaryHandler{
		videoSummaryService: videoSummaryService,
	}
}

/*
 * All Get methods for the SummaryHandler should be implemented here.
 * All of the methods are using DB ids to get the summary and video details.
 * The Get methods should return the domain objects, not the db objects.
 * The Get methods should return an error if the object is not found.
 * The Get methods should return an error if the input parameters are invalid.
 * The Get methods should return an error if the service returns an error.
 */

func (h *SummaryHandler) GetVideoSummaryByVideoID(ctx *gin.Context) {
	videoID := ctx.Param("videoID")
	videoID = strings.TrimSpace(videoID)
	if videoID == "" {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "videoID is required"})
		return
	}
	result, err := h.videoSummaryService.GetVideoSummaryByVideoID(ctx, videoID)
	if err != nil {
		if errors.Is(err, domain.ErrVideoNotFound) || errors.Is(err, domain.ErrSummaryNotFound) {
			ctx.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
			return
		}
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "internal server error"})
		return
	}
	ctx.JSON(200, result)
}

func (h *SummaryHandler) GetVideoSummaryByIDHandler(ctx *gin.Context) {
	summaryID := ctx.Param("summaryID")
	summaryID = strings.TrimSpace(summaryID)
	if summaryID == "" {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "summaryID is required"})
		return
	}

	result, err := h.videoSummaryService.GetVideoSummaryByID(ctx, summaryID)
	if err != nil {
		if errors.Is(err, domain.ErrVideoNotFound) || errors.Is(err, domain.ErrSummaryNotFound) {
			ctx.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
			return
		}
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "internal server error"})
		return
	}
	ctx.JSON(200, result)
}

/*
 * All Get methods for the SummaryHandler should be implemented here.
 * All of the methods are using video URLs to get the summary and video details.
 * The Get methods should return the domain objects, not the db objects.
 *
 * If the object is not found, create a backgroundtask to generate the summary
 * and return the TaskID of the task to the user.
 *
 * The Get methods should return an error if the input parameters are invalid.
 * The Get methods should return an error if the service returns an error.
 */

func (h *SummaryHandler) GetSummaryByVideoURL(ctx *gin.Context) {
	videoURL := ctx.Query("videoURL")
	videoURL = strings.TrimSpace(videoURL)
	if videoURL == "" {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "videoURL is required"})
		return
	}
	result, err := h.videoSummaryService.GetVideoSummaryByVideoURL(ctx, videoURL)
	if err != nil {
		if errors.Is(err, domain.ErrVideoNotFound) || errors.Is(err, domain.ErrSummaryNotFound) {
			ctx.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
			return
		}
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": "internal server error"})
		return
	}
	ctx.JSON(200, result)
}
