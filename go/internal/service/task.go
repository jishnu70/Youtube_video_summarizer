package service

// go/internal/service/task.go

import (
	"context"
	"errors"
	"strings"
	"time"

	"github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	repo "github.com/jishnu70/Youtube_video_summarizer/internal/repo"
)

type TaskService struct {
	taskRepo     *repo.TaskRepo
	cacheService *CacheService
}

func NewTaskService(taskRepo *repo.TaskRepo, cacheService *CacheService) (*TaskService, error) {
	if taskRepo == nil {
		return nil, errors.New("task repo is nil")
	}
	if cacheService == nil {
		return nil, errors.New("cache service is nil")
	}
	return &TaskService{
		taskRepo:     taskRepo,
		cacheService: cacheService,
	}, nil
}

func (s *TaskService) CreateTask(ctx context.Context, videoURL string) (*domain.BackgroundTaskStatus, error) {
	videoURL = strings.TrimSpace(videoURL)
	if videoURL == "" {
		return nil, errors.New("videoURL is empty")
	}
	now := time.Now().UTC()
	task := &domain.BackgroundTaskStatus{
		VideoURL:  videoURL,
		Status:    domain.TaskStatusQueued,
		CreatedAt: now,
		UpdatedAt: now,
	}
	result, err := s.taskRepo.Insert(ctx, task)
	if err != nil {
		return nil, err
	}
	err = s.cacheService.CacheTask(ctx, result.ID, result, 3600) // Cache for 1 hour
	if err != nil {
		return nil, err
	}
	err = s.cacheService.CacheVideoURLToTaskID(ctx, videoURL, result.ID, 3600) // Cache for 1 hou
	if err != nil {
		return nil, err
	}
	return result, nil
}

func (s *TaskService) GetTaskStatusByTaskID(ctx context.Context, taskID string) (*domain.BackgroundTaskStatus, error) {
	taskID = strings.TrimSpace(taskID)
	if taskID == "" {
		return nil, errors.New("taskID is empty")
	}
	task, err := s.cacheService.GetCachedTaskStatus(ctx, taskID)
	if err == nil {
		return task, nil
	}
	task, err = s.taskRepo.FindByID(ctx, taskID)
	if err != nil {
		return nil, err
	}
	err = s.cacheService.CacheTask(ctx, task.ID, task, 120) // Cache for 2 minutes
	if err != nil {
		return nil, err
	}
	return task, nil
}

func (s *TaskService) GetTaskStatusByVideoURL(ctx context.Context, videoURL string) (*domain.BackgroundTaskStatus, error) {
	videoURL = strings.TrimSpace(videoURL)
	if videoURL == "" {
		return nil, errors.New("videoURL is empty")
	}
	taskID, err := s.cacheService.GetCachedTaskIDByVideoURL(ctx, videoURL)
	if err == nil {
		result, err := s.cacheService.GetCachedTaskStatus(ctx, taskID)
		if err == nil {
			return result, nil
		}
	}
	result, err := s.taskRepo.FindByVideoURL(ctx, videoURL)
	if err != nil {
		return nil, err
	}
	err = s.cacheService.CacheTask(ctx, result.ID, result, 120) // Cache for 2 minutes
	if err != nil {
		return nil, err
	}
	err = s.cacheService.CacheVideoURLToTaskID(ctx, videoURL, result.ID, 3600) // Cache for 1 hour
	if err != nil {
		return nil, err
	}
	return result, nil
}
