package service

// go/internal/service/video_summary.go

import (
	"context"
	"errors"
	"strings"
	"time"

	domain "github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	repo "github.com/jishnu70/Youtube_video_summarizer/internal/repo"
)

type VideoSummaryService struct {
	videoRepo    *repo.VideoRepo
	summaryRepo  *repo.SummaryRepo
	cacheService *CacheService
}

func NewVideoSummaryService(
	videoRepo *repo.VideoRepo,
	summaryRepo *repo.SummaryRepo,
	cacheService *CacheService,
) (*VideoSummaryService, error) {
	if videoRepo == nil {
		return nil, errors.New("video repo is nil")
	}
	if summaryRepo == nil {
		return nil, errors.New("summary repo is nil")
	}
	if cacheService == nil {
		return nil, errors.New("cache service is nil")
	}
	return &VideoSummaryService{
		videoRepo:    videoRepo,
		summaryRepo:  summaryRepo,
		cacheService: cacheService,
	}, nil
}

/*
 * All Get methods for the VideoSummaryService should be implemented here.
 * The Get methods should return the domain objects, not the db objects.
 * The Get methods should return an error if the object is not found.
 * The Get methods should return an error if the input parameters are invalid.
 * The Get methods should return an error if the repo returns an error.
 */

func (s *VideoSummaryService) GetVideoSummaryByVideoID(ctx context.Context, videoID string) (*domain.VideoSummary, error) {
	videoSummary, err := s.cacheService.GetCachedVideoSummary(ctx, videoID)
	if err == nil {
		return videoSummary, nil
	}
	video, err := s.videoRepo.FindByID(ctx, videoID)
	if err != nil {
		return nil, err
	}
	summary, err := s.summaryRepo.FindByVideoID(ctx, videoID)
	if err != nil {
		return nil, err
	}
	return &domain.VideoSummary{
		Video:   video,
		Summary: summary,
	}, nil
}

func (s *VideoSummaryService) GetVideoSummaryByVideoURL(ctx context.Context, videoURL string) (*domain.VideoSummary, error) {
	video, err := s.videoRepo.FindByURL(ctx, videoURL)
	if err != nil {
		return nil, err
	}
	summary, err := s.summaryRepo.FindByVideoURL(ctx, videoURL)
	if err != nil {
		return nil, err
	}
	return &domain.VideoSummary{
		Video:   video,
		Summary: summary,
	}, nil
}

func (s *VideoSummaryService) GetVideoSummaryByID(ctx context.Context, id string) (*domain.VideoSummary, error) {
	summary, err := s.summaryRepo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	video, err := s.videoRepo.FindByID(ctx, summary.VideoID)
	if err != nil {
		return nil, err
	}
	return &domain.VideoSummary{
		Video:   video,
		Summary: summary,
	}, nil
}

func (s *VideoSummaryService) GetAllVideoSummaries(
	ctx context.Context,
	videoID string,
	lastID string,
	limit int64,
) ([]*domain.Summary, error) {
	videoID = strings.TrimSpace(videoID)
	if videoID == "" {
		return nil, errors.New("video ID is empty")
	}
	if limit <= 0 {
		limit = 10
	}
	return s.summaryRepo.FindAllByVideoID(ctx, videoID, lastID, limit)
}

func (s *VideoSummaryService) GetAllSummaries(
	ctx context.Context,
	lastID string,
	limit int64,
) ([]*domain.Summary, error) {
	if limit <= 0 {
		limit = 10
	}
	return s.summaryRepo.FindAllSummaries(ctx, nil, lastID, limit)
}

/*
 * All Create methods for the VideoSummaryService should be implemented here.
 * The Create methods should return the domain objects, not the db objects.
 * The Create methods should return an error if the input parameters are invalid.
 * The Create methods should return an error if the repo returns an error.
 */

func (s *VideoSummaryService) CreateVideo(ctx context.Context, videoURL string, transcript string) (*domain.Video, error) {
	videoURL = strings.TrimSpace(videoURL)
	if videoURL == "" {
		return nil, errors.New("video URL is empty")
	}
	now := time.Now().UTC()
	video := &domain.Video{
		VideoURL:   videoURL,
		Transcript: &transcript,
		CreatedAt:  now,
		UpdatedAt:  now,
	}
	return s.videoRepo.Insert(ctx, video)
}

func (s *VideoSummaryService) CreateSummary(ctx context.Context, summary *domain.Summary) (*domain.Summary, error) {
	video, err := s.videoRepo.FindByID(ctx, summary.VideoID)
	if err != nil {
		return nil, err
	}
	if video.VideoURL != summary.VideoUrl {
		return nil, errors.New("video URL does not match the video ID")
	}
	now := time.Now().UTC()
	summary.CreatedAt = now
	return s.summaryRepo.Insert(ctx, summary)
}
