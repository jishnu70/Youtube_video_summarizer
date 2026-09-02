package domain

// go/internal/domain/constants.go

import "errors"

var ErrTaskNotFound = errors.New("task not found")
var ErrVideoNotFound = errors.New("video not found")
var ErrSummaryNotFound = errors.New("summary not found")
var ErrCacheMiss = errors.New("cache miss")

type TaskStatus string

const (
	TaskStatusQueued       TaskStatus = "QUEUED"
	TaskStatusStarted      TaskStatus = "STARTED"
	TaskStatusDownloading  TaskStatus = "DOWNLOADING"
	TaskStatusTranscribing TaskStatus = "TRANSCRIBING"
	TaskStatusProcessing   TaskStatus = "PROCESSING"
	TaskStatusCompleted    TaskStatus = "COMPLETED"
	TaskStatusFailed       TaskStatus = "FAILED"
	TaskStatusTimedOut     TaskStatus = "TIMEOUT"
	TaskStatusCancelled    TaskStatus = "CANCELLED"
	TaskStatusUnknown      TaskStatus = "UNKNOWN"
)

// helper to check if valid TaskStatus
func (ts TaskStatus) IsValid() bool {
	switch ts {
	case TaskStatusQueued,
		TaskStatusProcessing,
		TaskStatusCompleted,
		TaskStatusFailed,
		TaskStatusTimedOut,
		TaskStatusCancelled,
		TaskStatusUnknown:
		return true
	default:
		return false
	}
}
