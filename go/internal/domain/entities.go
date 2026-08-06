package domain

// go/internal/domain/entities.go

import (
	"time"
)

type Video struct {
	ID         string
	VideoURL   string
	Transcript *string
	CreatedAt  time.Time
	UpdatedAt  time.Time
}

type Summary struct {
	ID        string
	VideoID   string
	VideoUrl  string
	Summary   string
	ModelName string
	CreatedAt time.Time
}

type VideoSummary struct {
	Video   *Video
	Summary *Summary
}

type BackgroundTaskStatus struct {
	ID        string
	VideoID   string
	Message   string
	Status    TaskStatus
	CreatedAt time.Time
	UpdatedAt time.Time
}
