package db

// go/internal/db/models.go

import (
	"time"

	"github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	"go.mongodb.org/mongo-driver/v2/bson"
)

/*
 * DB struct representing the Video entity in the database.
 */
type VideoDB struct {
	ID         bson.ObjectID `bson:"_id" json:"id"`
	VideoURL   string        `bson:"video_url" json:"video_url"`
	Transcript *string       `bson:"transcript,omitempty" json:"transcript,omitempty"`
	CreatedAt  time.Time     `bson:"created_at" json:"created_at"`
	UpdatedAt  time.Time     `bson:"updated_at" json:"updated_at"`

	// transcript is optional, so we use a pointer to string to allow nil values
	// when the video is first created and the transcript is not yet available.
	// we need a base data struct to represent the video entity
	// the moment Transcript is available, we can update the Video entity with the transcript.
}

func (v *VideoDB) ToDomain() *domain.Video {
	return &domain.Video{
		ID:         v.ID.Hex(),
		VideoURL:   v.VideoURL,
		Transcript: v.Transcript,
		CreatedAt:  v.CreatedAt,
		UpdatedAt:  v.UpdatedAt,
	}
}

// NewSummaryDB is a struct for inserting:
// - video_id of the video
// - video_url of the video
// - summary of video
// - model_name of the model used to generate the summary
// - created_at timestamp of when the summary was created
type SummaryDB struct {
	ID        bson.ObjectID `bson:"_id" json:"id"`
	VideoID   bson.ObjectID `bson:"video_id" json:"video_id"`
	VideoUrl  string        `bson:"video_url" json:"video_url"`
	Summary   string        `bson:"summary" json:"summary"`
	ModelName string        `bson:"model_name" json:"model_name"`
	CreatedAt time.Time     `bson:"created_at" json:"created_at"`
}

func (s *SummaryDB) ToDomain() *domain.Summary {
	return &domain.Summary{
		ID:        s.ID.Hex(),
		VideoID:   s.VideoID.Hex(),
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
	VideoID   string            `bson:"video_id" json:"video_id"`
	Status    domain.TaskStatus `bson:"status" json:"status"`
	Message   *string           `bson:"message,omitempty" json:"message,omitempty"`
	CreatedAt time.Time         `bson:"created_at" json:"created_at"`
	UpdatedAt time.Time         `bson:"updated_at" json:"updated_at"`
}

func (b *BackgroundTaskStatusDB) ToDomain() *domain.BackgroundTaskStatus {
	message := ""
	if b.Message != nil {
		message = *b.Message
	}
	return &domain.BackgroundTaskStatus{
		ID:        b.ID.Hex(),
		VideoID:   b.VideoID,
		Status:    b.Status,
		Message:   message,
		CreatedAt: b.CreatedAt,
		UpdatedAt: b.UpdatedAt,
	}
}
