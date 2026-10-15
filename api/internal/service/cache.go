package service

// api/internal/service/cache.go

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	repo "github.com/jishnu70/Youtube_video_summarizer/internal/repo"
)

type CacheService struct {
	cacheRepo *repo.CacheRepo
}

func NewCacheService(cacheRepo *repo.CacheRepo) (*CacheService, error) {
	if cacheRepo == nil {
		return nil, domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			"CacheService: cacheRepo is nil",
			fmt.Errorf("cacheRepo is nil"),
		)
	}
	return &CacheService{
		cacheRepo: cacheRepo,
	}, nil
}

type cacheType string

const (
	SummaryCacheKeyPrefix  cacheType = "summary:"
	CacheTaskIDPrefix      cacheType = "task:id:"
	CacheURLToTaskIDPrefix cacheType = "task:url:"
)

func generateCacheKey(videoURL string, keyType cacheType) string {
	return string(keyType) + videoURL
}

func structToString(value any) ([]byte, error) {
	jsonBytes, err := json.Marshal(value)
	if err != nil {
		return nil, domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInternalError,
			"CacheService: failed to marshal struct to JSON",
			err,
		)
	}
	return jsonBytes, nil
}

func stringToStruct(data []byte, value any) error {
	if err := json.Unmarshal(data, value); err != nil {
		return domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInternalError,
			"CacheService: failed to unmarshal JSON to struct",
			err,
		)
	}
	return nil
}

func (s *CacheService) setCache(ctx context.Context, key string, value any, keyType cacheType, ttl int64) error {
	key = strings.TrimSpace(key)
	if key == "" {
		return domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			"CacheService: cache key is empty",
			fmt.Errorf("cache key is empty"),
		)
	}
	if value == nil {
		return domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			"CacheService: cache value is nil",
			fmt.Errorf("cache value is nil"),
		)
	}
	payload, err := structToString(value)
	if err != nil {
		return err
	}
	return s.cacheRepo.Set(ctx, generateCacheKey(key, keyType), payload, ttl)
}

func (s *CacheService) getCache(ctx context.Context, key string, value any, keyType cacheType) error {
	key = strings.TrimSpace(key)
	if key == "" {
		return domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			"CacheService: cache key is empty",
			fmt.Errorf("cache key is empty"),
		)
	}
	data, err := s.cacheRepo.Get(ctx, generateCacheKey(key, keyType))
	if err != nil {
		return err
	}
	return stringToStruct(data, value)
}

func (s *CacheService) CacheSummary(ctx context.Context, videoURL string, value *domain.Summary, ttl int64) error {
	if err := s.setCache(ctx, videoURL, value, SummaryCacheKeyPrefix, ttl); err != nil {
		return fmt.Errorf("failed to cache summary: %w", err)
	}
	return nil
}

func (s *CacheService) CacheTask(ctx context.Context, taskID string, value *domain.BackgroundTaskStatus, ttl int64) error {
	if err := s.setCache(ctx, taskID, value, CacheTaskIDPrefix, ttl); err != nil {
		return fmt.Errorf("failed to cache task: %w", err)
	}
	return nil
}

func (r *CacheService) CacheVideoURLToTaskID(ctx context.Context, videoURL string, taskID string, ttl int64) error {
	videoURL = strings.TrimSpace(videoURL)
	if videoURL == "" {
		return domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			fmt.Sprintf("CacheService: %s", domain.ErrVideoURLEmpty),
			fmt.Errorf("videoURL is empty"),
		)
	}
	taskID = strings.TrimSpace(taskID)
	if taskID == "" {
		return domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			fmt.Sprintf("CacheService: %s", domain.ErrTaskIDEmpty),
			fmt.Errorf("taskID is empty"),
		)
	}
	if err := r.cacheRepo.Set(ctx, generateCacheKey(videoURL, CacheURLToTaskIDPrefix), taskID, ttl); err != nil {
		return fmt.Errorf("failed to cache videoURL to taskID mapping: %w", err)
	}
	return nil
}

func (s *CacheService) GetCachedSummary(ctx context.Context, videoURL string) (*domain.Summary, error) {
	var summary domain.Summary
	if err := s.getCache(ctx, videoURL, &summary, SummaryCacheKeyPrefix); err != nil {
		return nil, fmt.Errorf("failed to get cached summary: %w", err)
	}
	return &summary, nil
}

func (s *CacheService) GetCachedTaskIDByVideoURL(ctx context.Context, videoURL string) (string, error) {
	videoURL = strings.TrimSpace(videoURL)
	if videoURL == "" {
		return "", domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			fmt.Sprintf("CacheService: %s", domain.ErrVideoURLEmpty),
			fmt.Errorf("videoURL is empty"),
		)
	}
	taskID, err := s.cacheRepo.Get(ctx, generateCacheKey(videoURL, CacheURLToTaskIDPrefix))
	if err != nil {
		return "", fmt.Errorf("failed to get cached taskID by videoURL: %w", err)
	}
	return string(taskID), nil
}

func (s *CacheService) GetCachedTaskStatus(ctx context.Context, taskID string) (*domain.BackgroundTaskStatus, error) {
	var taskStatus domain.BackgroundTaskStatus
	if err := s.getCache(ctx, taskID, &taskStatus, CacheTaskIDPrefix); err != nil {
		return nil, fmt.Errorf("failed to get cached task status with id %s: %w", taskID, err)
	}
	return &taskStatus, nil
}
