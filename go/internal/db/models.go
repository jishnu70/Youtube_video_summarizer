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
	ID         bson.ObjectID `bson:"_id"`
	URL        string        `bson:"url"`
	Transcript *string       `bson:"transcript,omitempty"`
	// transcript is optional, so we use a pointer to string to allow nil values
	// when the video is first created and the transcript is not yet available.
	// we need a base data struct to represent the video entity
	// the moment Transcript is available, we can update the Video entity with the transcript.
	CreatedAt time.Time `bson:"created_at"`
	UpdatedAt time.Time `bson:"updated_at"`
}

func (v *VideoDB) ToDomain() *domain.Video {
	id := v.ID.Hex()
	return &domain.Video{
		ID:         &id,
		URL:        v.URL,
		Transcript: v.Transcript,
		CreatedAt:  v.CreatedAt,
		UpdatedAt:  v.UpdatedAt,
	}
}

/*
 * DB struct representing the Summary entity in the database.
 * SummaryObject is a nested struct within SummaryDB to represent the summary details.
 * SummaryDBList is a struct for a list of summaries for a video, including the video ID and URL.
 * SummaryDB is a struct for a single summary for a video, including the video ID and summary details.
 */
type SummaryObject struct {
	Summary   string    `bson:"summary"`
	ModelName string    `bson:"model_name"`
	CreatedAt time.Time `bson:"created_at"`
}

type SummaryDBList struct {
	ID        bson.ObjectID    `bson:"_id"`
	VideoID   bson.ObjectID    `bson:"video_id"`
	VideoUrl  string           `bson:"video_url"`
	Summaries []*SummaryObject `bson:"summaries"`
}

type SummaryDB struct {
	ID       bson.ObjectID `bson:"_id"`
	VideoID  bson.ObjectID `bson:"video_id"`
	VideoUrl string        `bson:"video_url"`
	Summary  SummaryObject `bson:"summaryObject"`
}

func (s *SummaryDB) ToDomain() *domain.Summary {
	return &domain.Summary{
		ID:        s.ID.Hex(),
		VideoID:   s.VideoID.Hex(),
		Summary:   s.Summary.Summary,
		ModelName: s.Summary.ModelName,
		CreatedAt: s.Summary.CreatedAt,
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
	ID        bson.ObjectID     `bson:"_id"`
	TaskID    string            `bson:"task_id"`
	URL       string            `bson:"url"`
	Video     *VideoDB          `bson:"video,omitempty"`
	Status    domain.TaskStatus `bson:"status"`
	Message   *string           `bson:"message,omitempty"`
	CreatedAt time.Time         `bson:"created_at"`
	UpdatedAt time.Time         `bson:"updated_at"`
}

func (b *BackgroundTaskStatusDB) ToDomain() *domain.BackgroundTaskStatus {
	var video *domain.Video
	if b.Video != nil {
		video = b.Video.ToDomain()
	}
	return &domain.BackgroundTaskStatus{
		ID:        b.ID.Hex(),
		TaskID:    b.TaskID,
		URL:       b.URL,
		Video:     video,
		Status:    b.Status,
		Message:   b.Message,
		CreatedAt: b.CreatedAt,
		UpdatedAt: b.UpdatedAt,
	}
}
