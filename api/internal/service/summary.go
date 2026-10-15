package service

// api/internal/service/summary.go

import (
	"context"
	"fmt"
	"strings"

	"github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	repo "github.com/jishnu70/Youtube_video_summarizer/internal/repo"
)

type SummaryService struct {
	summaryRepo  *repo.SummaryRepo
	cacheService *CacheService
}

func NewSummaryService(
	summaryRepo *repo.SummaryRepo,
	cacheService *CacheService,
) (*SummaryService, error) {
	if summaryRepo == nil {
		return nil, domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			"SummaryService: summaryRepo is nil",
			fmt.Errorf("summaryRepo is nil"),
		)
	}
	if cacheService == nil {
		return nil, domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			"SummaryService: cacheService is nil",
			fmt.Errorf("cacheService is nil"),
		)
	}
	return &SummaryService{
		summaryRepo:  summaryRepo,
		cacheService: cacheService,
	}, nil
}

func (s *SummaryService) GetSummaryByVideoURL(ctx context.Context, videoURL string) (*domain.Summary, error) {
	// Check if the videoURL is empty
	videoURL = strings.TrimSpace(videoURL)
	if videoURL == "" {
		return nil, domain.NewAppError(
			domain.ServiceLayer,
			domain.CodeInvalidInput,
			fmt.Sprintf("SummaryService: %s", domain.ErrVideoURLEmpty),
			fmt.Errorf("videoURL is empty"),
		)
	}

	// Check if the summary is in the cache
	summary, err := s.cacheService.GetCachedSummary(ctx, videoURL)
	if err == nil {
		return summary, nil
	}

	// If not in cache, fetch from the database
	summary, err = s.summaryRepo.FindByVideoURL(ctx, videoURL)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch summary from database: %w", err)
	}

	// Cache the summary for future requests
	err = s.cacheService.CacheSummary(ctx, videoURL, summary, 10)
	if err != nil {
		return summary, fmt.Errorf("failed to cache summary: %w", err)
	}
	return summary, nil
}
