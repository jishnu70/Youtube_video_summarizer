package handler

// api/requests/handler/handler.go

import (
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"time"

	"github.com/gin-gonic/gin"
	domain "github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	service "github.com/jishnu70/Youtube_video_summarizer/internal/service"
	schema "github.com/jishnu70/Youtube_video_summarizer/requests/schema"
)

type RequestHandler struct {
	summaryService *service.SummaryService
	taskService    *service.TaskService
}

func NewRequestHandler(
	summaryService *service.SummaryService,
	taskService *service.TaskService,
) *RequestHandler {
	if summaryService == nil {
		panic("summaryService is nil")
	}
	if taskService == nil {
		panic("taskService is nil")
	}
	return &RequestHandler{
		summaryService: summaryService,
		taskService:    taskService,
	}
}

func (h *RequestHandler) GetSummary(ctx *gin.Context) {
	var videoURLBinding schema.SummaryRequest
	if err := ctx.ShouldBindQuery(&videoURLBinding); err != nil {
		ctx.Error(err)
		return
	}

	summary, err := h.summaryService.GetSummaryByVideoURL(ctx.Request.Context(), videoURLBinding.VideoURL)
	if err != nil {
		if errors.Is(err, domain.ErrSummaryNotFound) {
			if exists, checkErr := checkYouTubeVideoExists(videoURLBinding.VideoURL); checkErr != nil {
				ctx.Error(checkErr)
				return
			} else if !exists {
				ctx.JSON(http.StatusNotFound, gin.H{"error": "YouTube video does not exist."})
				return
			}

			// Create a new background task for the video
			task, taskErr := h.taskService.CreateTask(ctx.Request.Context(), videoURLBinding.VideoURL)
			if taskErr != nil {
				ctx.Error(fmt.Errorf("failed to create background task: %w", taskErr))
				return
			}
			ctx.JSON(http.StatusAccepted, schema.NewTaskStatusResponse(task))
			return
		}
		ctx.Error(err)
		return
	}

	ctx.JSON(http.StatusOK, schema.NewSummaryResponse(summary))
}

func (h *RequestHandler) GetTaskStatus(ctx *gin.Context) {
	var taskIDBinding schema.TaskStatusRequest
	if err := ctx.ShouldBindQuery(&taskIDBinding); err != nil {
		ctx.JSON(400, gin.H{"error": err.Error()})
		return
	}

	taskID := taskIDBinding.TaskID
	videoURL := taskIDBinding.VideoURL
	if taskID == "" && videoURL == "" {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request: insufficient parameters provided."})
		return
	}

	var taskStatus *domain.BackgroundTaskStatus
	var err error
	if taskID != "" {
		taskStatus, err = h.taskService.GetTaskStatusByTaskID(ctx.Request.Context(), taskID)
	} else {
		taskStatus, err = h.taskService.GetTaskStatusByVideoURL(ctx.Request.Context(), videoURL)
	}

	if err != nil {
		ctx.Error(err)
		return
	}

	if taskStatus == nil {
		ctx.Error(domain.ErrTaskNotFound)
		return
	}

	ctx.JSON(http.StatusOK, schema.NewTaskStatusResponse(taskStatus))
}

func checkYouTubeVideoExists(videoURL string) (bool, error) {
	// Build the oEmbed endpoint URL

	_, err := url.ParseRequestURI(videoURL)
	if err != nil {
		return false, fmt.Errorf("invalid video URL: %w", err)
	}

	oembedBaseURL := "https://www.youtube.com/oembed"
	params := url.Values{}
	params.Set("url", videoURL)
	oembedURL := fmt.Sprintf("%s?%s", oembedBaseURL, params.Encode())

	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Get(oembedURL)
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()

	// If the video doesn't exist, is private, or is deleted,
	// the oEmbed API reliably returns a 404 Not Found or 400 Bad Request.
	if resp.StatusCode == http.StatusOK {
		return true, nil
	}

	return false, nil
}
