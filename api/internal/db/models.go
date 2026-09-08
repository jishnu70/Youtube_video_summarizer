package db

// api/internal/db/models.go

import (
	"time"

	"github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	"go.mongodb.org/mongo-driver/v2/bson"
)

// NewSummaryDB is a struct for inserting:
// - video_id of the video
// - video_url of the video
// - summary of video
// - model_name of the model used to generate the summary
// - created_at timestamp of when the summary was created
type SummaryDB struct {
	ID        bson.ObjectID `bson:"_id" json:"id"`
	VideoURL  string        `bson:"video_url" json:"video_url"`
	Summary   string        `bson:"summary" json:"summary"`
	ModelName string        `bson:"model_name" json:"model_name"`
	CreatedAt time.Time     `bson:"created_at" json:"created_at"`
}

func (s *SummaryDB) ToDomain() *domain.Summary {
	return &domain.Summary{
		ID:        s.ID.Hex(),
		VideoURL:  s.VideoURL,
		Summary:   s.Summary,
		ModelName: s.ModelName,
		CreatedAt: s.CreatedAt,
	}
}

/*
 * DB struct representing the BackgroundTaskStatus entity in the database.
 * BackgroundTaskStatusDB is a struct for a background task status:
 * 	TaskID: unique identifier for the task
 * 	URL: the URL of the video being processed
 * 	Video: optional VideoDB struct representing the video being processed
 * 	Status: the current status of the task (queued, started, processing, completed, failed, timeout, cancelled, unknown)
 * 	Message: optional message providing additional information about the task status
 * 	CreatedAt: timestamp when the task was created
 * 	UpdatedAt: timestamp when the task was last updated
 */
type BackgroundTaskStatusDB struct {
	ID        bson.ObjectID     `bson:"_id" json:"id"`
	VideoURL  string            `bson:"video_url" json:"video_url"`
	Message   string            `bson:"message" json:"message"`
	Status    domain.TaskStatus `bson:"status" json:"status"`
	CreatedAt time.Time         `bson:"created_at" json:"created_at"`
	UpdatedAt time.Time         `bson:"updated_at" json:"updated_at"`
}

func (b *BackgroundTaskStatusDB) ToDomain() *domain.BackgroundTaskStatus {
	return &domain.BackgroundTaskStatus{
		ID:        b.ID.Hex(),
		VideoURL:  b.VideoURL,
		Message:   b.Message,
		Status:    b.Status,
		CreatedAt: b.CreatedAt,
		UpdatedAt: b.UpdatedAt,
	}
}
