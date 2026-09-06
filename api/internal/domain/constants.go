package domain

// api/internal/domain/constants.go

type TaskStatus string

const (
	TaskStatusQueued       TaskStatus = "QUEUED"
	TaskStatusStarted      TaskStatus = "STARTED"
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
		TaskStatusUnknown,
		TaskStatusStarted,
		TaskStatusTranscribing:
		return true
	default:
		return false
	}
}

// constants for TTL
const (
	CacheTTLSeconds = 3600 // 1 hour
)
