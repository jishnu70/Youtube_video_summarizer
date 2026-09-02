package service

// go/internal/service/cache.go

import (
	"context"
	"encoding/json"
	"errors"
	"strings"

	"github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	repo "github.com/jishnu70/Youtube_video_summarizer/internal/repo"
	"github.com/redis/go-redis/v9"
)

type CacheService struct {
	cacheRepo *repo.CacheRepo
}

func NewCacheService(cacheRepo *repo.CacheRepo) (*CacheService, error) {
	if cacheRepo == nil {
		return nil, errors.New("cache repo is nil")
	}
	return &CacheService{
		cacheRepo: cacheRepo,
	}, nil
}

type cacheType string

const (
	VideoCacheKeyPrefix        cacheType = "video:"
	SummaryCacheKeyPrefix      cacheType = "summary:"
	TaskCacheKeyPrefix         cacheType = "task:"
	VideoSummaryCacheKeyPrefix cacheType = "video_summary:"
)

func generateCacheKey(videoURL string, keyType cacheType) string {
	return string(keyType) + videoURL
}

func structToString(value any) ([]byte, error) {
	jsonBytes, err := json.Marshal(value)
	if err != nil {
		return nil, err
	}
	return jsonBytes, nil
}

func stringToStruct(data []byte, value any) error {
	if err := json.Unmarshal(data, value); err != nil {
		return err
	}
	return nil
}

func (s *CacheService) setCache(ctx context.Context, key string, value any, keyType cacheType, ttl int64) error {
	if strings.TrimSpace(key) == "" {
		return errors.New("cache key is empty")
	}
	if value == nil {
		return errors.New("cache value is nil")
	}
	payload, err := structToString(value)
	if err != nil {
		return err
	}
	return s.cacheRepo.Set(ctx, generateCacheKey(key, keyType), payload, ttl)
}

func (s *CacheService) getCache(ctx context.Context, key string, value any, keyType cacheType) error {
	if strings.TrimSpace(key) == "" {
		return errors.New("cache key is empty")
	}
	data, err := s.cacheRepo.Get(ctx, generateCacheKey(key, keyType))
	if err != nil {
		if errors.Is(err, redis.Nil) {
			return domain.ErrCacheMiss
		}
		return err
	}
	return stringToStruct([]byte(data), value)
}

func (s *CacheService) CacheVideo(ctx context.Context, videoURL string, value *domain.Video, ttl int64) error {
	return s.setCache(ctx, videoURL, value, VideoCacheKeyPrefix, ttl)
}

func (s *CacheService) CacheSummary(ctx context.Context, videoURL string, value *domain.Summary, ttl int64) error {
	return s.setCache(ctx, videoURL, value, SummaryCacheKeyPrefix, ttl)
}

func (s *CacheService) CacheVideoSummary(ctx context.Context, videoID string, value *domain.VideoSummary, ttl int64) error {
	return s.setCache(ctx, videoID, value, VideoSummaryCacheKeyPrefix, ttl)
}

func (s *CacheService) CacheTask(ctx context.Context, taskID string, value *domain.BackgroundTaskStatus, ttl int64) error {
	return s.setCache(ctx, taskID, value, TaskCacheKeyPrefix, ttl)
}

func (r *CacheService) CacheVideoURLToTaskID(ctx context.Context, videoURL string, taskID string, ttl int64) error {
	if strings.TrimSpace(videoURL) == "" {
		return errors.New("video URL is empty")
	}
	if strings.TrimSpace(taskID) == "" {
		return errors.New("task ID is empty")
	}
	return r.cacheRepo.Set(ctx, generateCacheKey(videoURL, TaskCacheKeyPrefix), taskID, ttl)
}

func (s *CacheService) GetCachedVideo(ctx context.Context, videoURL string) (*domain.Video, error) {
	var video domain.Video
	if err := s.getCache(ctx, videoURL, &video, VideoCacheKeyPrefix); err != nil {
		return nil, err
	}
	return &video, nil
}

func (s *CacheService) GetCachedSummary(ctx context.Context, videoURL string) (*domain.Summary, error) {
	var summary domain.Summary
	if err := s.getCache(ctx, videoURL, &summary, SummaryCacheKeyPrefix); err != nil {
		return nil, err
	}
	return &summary, nil
}

func (s *CacheService) GetCachedVideoSummary(ctx context.Context, videoID string) (*domain.VideoSummary, error) {
	var videoSummary domain.VideoSummary
	if err := s.getCache(ctx, videoID, &videoSummary, VideoSummaryCacheKeyPrefix); err != nil {
		return nil, err
	}
	return &videoSummary, nil
}

func (s *CacheService) GetCachedTaskIDByVideoURL(ctx context.Context, videoURL string) (string, error) {
	if strings.TrimSpace(videoURL) == "" {
		return "", errors.New("video URL is empty")
	}
	taskID, err := s.cacheRepo.Get(ctx, generateCacheKey(videoURL, TaskCacheKeyPrefix))
	if err != nil {
		if errors.Is(err, redis.Nil) {
			return "", domain.ErrCacheMiss
		}
		return "", err
	}
	return taskID, nil
}

func (s *CacheService) GetCachedTaskStatus(ctx context.Context, taskID string) (*domain.BackgroundTaskStatus, error) {
	var taskStatus domain.BackgroundTaskStatus
	if err := s.getCache(ctx, taskID, &taskStatus, TaskCacheKeyPrefix); err != nil {
		return nil, err
	}
	return &taskStatus, nil
}

func (s *CacheService) DeleteCachedVideo(ctx context.Context, videoURL string) error {
	return s.cacheRepo.Delete(ctx, generateCacheKey(videoURL, VideoCacheKeyPrefix))
}

func (s *CacheService) DeleteCachedSummary(ctx context.Context, videoURL string) error {
	return s.cacheRepo.Delete(ctx, generateCacheKey(videoURL, SummaryCacheKeyPrefix))
}

func (s *CacheService) DeleteCachedTaskStatus(ctx context.Context, videoURL string) error {
	return s.cacheRepo.Delete(ctx, generateCacheKey(videoURL, TaskCacheKeyPrefix))
}
