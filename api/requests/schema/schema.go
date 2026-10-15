package schema

// api/requests/schema/schema.go

import (
	"time"

	domain "github.com/jishnu70/Youtube_video_summarizer/internal/domain"
)

type SummaryRequest struct {
	VideoURL string `form:"video_url" binding:"required,url"`
}

type SummaryResponse struct {
	ID        string    `json:"id"`
	VideoURL  string    `json:"video_url"`
	Summary   string    `json:"summary"`
	ModelName string    `json:"model_name"`
	CreatedAt time.Time `json:"created_at"`
}

func NewSummaryResponse(summary *domain.Summary) *SummaryResponse {
	return &SummaryResponse{
		ID:        summary.ID,
		VideoURL:  summary.VideoURL,
		Summary:   summary.Summary,
		ModelName: summary.ModelName,
		CreatedAt: summary.CreatedAt,
	}
}

type TaskStatusRequest struct {
	TaskID   string `form:"task_id,omitempty"`
	VideoURL string `form:"video_url,omitempty"`
}

type TaskStatusResponse struct {
	ID        string    `json:"id"`
	VideoURL  string    `json:"video_url"`
	Message   string    `json:"message"`
	Status    string    `json:"status"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

func NewTaskStatusResponse(task *domain.BackgroundTaskStatus) *TaskStatusResponse {
	return &TaskStatusResponse{
		ID:        task.ID,
		VideoURL:  task.VideoURL,
		Message:   task.Message,
		Status:    string(task.Status),
		CreatedAt: task.CreatedAt,
		UpdatedAt: task.UpdatedAt,
	}
}
