package service

// api/internal/service/task.go

import (
	"context"
	"fmt"
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
		return nil, domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			"TaskService: taskRepo is nil",
			fmt.Errorf("taskRepo is nil"),
		)
	}
	if cacheService == nil {
		return nil, domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			"TaskService: cacheService is nil",
			fmt.Errorf("cacheService is nil"),
		)
	}
	return &TaskService{
		taskRepo:     taskRepo,
		cacheService: cacheService,
	}, nil
}

func (s *TaskService) CreateTask(ctx context.Context, videoURL string) (*domain.BackgroundTaskStatus, error) {
	videoURL = strings.TrimSpace(videoURL)
	if videoURL == "" {
		return nil, domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			fmt.Sprintf("TaskService: %s", domain.ErrVideoURLEmpty),
			fmt.Errorf("videoURL is empty"),
		)
	}
	now := time.Now().UTC()
	task := &domain.BackgroundTaskStatus{
		VideoURL:  videoURL,
		Message:   "The video is queued for processing",
		Status:    domain.TaskStatusQueued,
		CreatedAt: now,
		UpdatedAt: now,
	}
	result, err := s.taskRepo.Insert(ctx, task)
	if err != nil {
		return nil, fmt.Errorf("failed to create task: %w", err)
	}
	err = s.cacheService.CacheTask(ctx, result.ID, result, 3600) // Cache for 1 hour
	if err != nil {
		return nil, fmt.Errorf("failed to cache task: %w", err)
	}
	err = s.cacheService.CacheVideoURLToTaskID(ctx, videoURL, result.ID, 3600) // Cache for 1 hou
	if err != nil {
		return nil, fmt.Errorf("failed to cache videoURL to taskID mapping: %w", err)
	}
	return result, nil
}

func (s *TaskService) GetTaskStatusByTaskID(ctx context.Context, taskID string) (*domain.BackgroundTaskStatus, error) {
	taskID = strings.TrimSpace(taskID)
	if taskID == "" {
		return nil, domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			fmt.Sprintf("TaskService: %s", domain.ErrTaskIDEmpty),
			fmt.Errorf("taskID is empty"),
		)
	}
	task, err := s.cacheService.GetCachedTaskStatus(ctx, taskID)
	if err == nil {
		return task, nil
	}
	task, err = s.taskRepo.FindByID(ctx, taskID)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch task from database: %w", err)
	}
	err = s.cacheService.CacheTask(ctx, task.ID, task, 120) // Cache for 2 minutes
	if err != nil {
		return task, fmt.Errorf("failed to cache task: %w", err)
	}
	return task, nil
}

func (s *TaskService) GetTaskStatusByVideoURL(ctx context.Context, videoURL string) (*domain.BackgroundTaskStatus, error) {
	videoURL = strings.TrimSpace(videoURL)
	if videoURL == "" {
		return nil, domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			fmt.Sprintf("TaskService: %s", domain.ErrVideoURLEmpty),
			fmt.Errorf("videoURL is empty"),
		)
	}
	taskID, err := s.cacheService.GetCachedTaskIDByVideoURL(ctx, videoURL)
	if err == nil {
		result, err := s.cacheService.GetCachedTaskStatus(ctx, taskID)
		if err != nil {
			return s.GetTaskStatusByTaskID(ctx, taskID)
		}
		return result, nil
	}
	result, err := s.taskRepo.FindByVideoURL(ctx, videoURL)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch task from database: %w", err)
	}
	err = s.cacheService.CacheTask(ctx, result.ID, result, 120) // Cache for 2 minutes
	if err != nil {
		return result, fmt.Errorf("failed to cache task: %w", err)
	}
	err = s.cacheService.CacheVideoURLToTaskID(ctx, videoURL, result.ID, 3600) // Cache for 1 hour
	if err != nil {
		return result, fmt.Errorf("failed to cache videoURL to taskID mapping: %w", err)
	}
	return result, nil
}
