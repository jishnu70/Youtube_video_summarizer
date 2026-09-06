package domain

// api/internal/domain/entities.go

import (
	"time"
)

type Summary struct {
	ID        string
	VideoURL  string
	Summary   string
	ModelName string
	CreatedAt time.Time
}

type BackgroundTaskStatus struct {
	ID        string
	VideoURL  string
	Message   string
	Status    TaskStatus
	CreatedAt time.Time
	UpdatedAt time.Time
}
