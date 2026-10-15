package repo

// api/internal/repo/cache.go

import (
	"context"
	"errors"
	"fmt"
	"time"

	domain "github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	redis "github.com/redis/go-redis/v9"
)

type CacheRepo struct {
	client *redis.Client
}

func NewCacheRepo(redisClient *redis.Client) *CacheRepo {
	return &CacheRepo{
		client: redisClient,
	}
}

type method string

const (
	GET method = "GET"
	SET method = "SET"
	DEL method = "DEL"
)

var metToStr = map[method]string{
	GET: domain.ErrCacheGetFailed,
	SET: domain.ErrCacheSetFailed,
	DEL: domain.ErrCacheDeleteFailed,
}

func handleRedisError(err error, met method) error {
	if errors.Is(err, redis.ErrPoolTimeout) {
		return domain.NewAppError(
			domain.CacheLayer,
			domain.ErrCacheConnectionTimeout,
			fmt.Sprintf("CacheRepo: %s", domain.ErrCacheConnectionTimeout),
			err,
		)
	}
	if errors.Is(err, redis.ErrClosed) {
		return domain.NewAppError(
			domain.CacheLayer,
			domain.ErrCacheConnectionFailed,
			fmt.Sprintf("CacheRepo: %s", domain.ErrCacheConnectionFailed),
			err,
		)
	}
	if errors.Is(err, redis.Nil) {
		return domain.NewAppError(
			domain.CacheLayer,
			domain.ErrCacheKeyNotFound,
			fmt.Sprintf("CacheRepo: %s", domain.ErrCacheKeyNotFound),
			err,
		)
	}
	return domain.NewAppError(
		domain.CacheLayer,
		domain.ErrCacheGetFailed,
		fmt.Sprintf("CacheRepo: %s", metToStr[met]),
		err,
	)
}

func (r *CacheRepo) Set(ctx context.Context, key string, value any, ttl int64) error {
	duration := time.Duration(ttl) * time.Second
	if err := r.client.Set(ctx, key, value, duration).Err(); err != nil {
		return handleRedisError(err, SET)
	}
	return nil
}

func (r *CacheRepo) SetNx(ctx context.Context, key string, value any, ttl int64) (bool, error) {
	duration := time.Duration(ttl) * time.Second
	isSet, err := r.client.SetNX(ctx, key, value, duration).Result()
	// isSet will be true if the key was set, false if it already exists
	if err != nil {
		return false, handleRedisError(err, SET)
	}
	return isSet, nil
}

func (r *CacheRepo) Get(ctx context.Context, key string) ([]byte, error) {
	value, err := r.client.Get(ctx, key).Bytes()
	if err != nil {
		return nil, handleRedisError(err, GET)
	}
	return value, nil
}

func (r *CacheRepo) GetTTl(ctx context.Context, key string) (time.Duration, error) {
	ttl, err := r.client.TTL(ctx, key).Result()
	if err != nil {
		return 0, handleRedisError(err, GET)
	}
	return ttl, nil
}

func (r *CacheRepo) Exists(ctx context.Context, key string) (bool, error) {
	exists, err := r.client.Exists(ctx, key).Result()
	if err != nil {
		return false, handleRedisError(err, GET)
	}
	return exists > 0, nil
}

func (r *CacheRepo) Delete(ctx context.Context, key string) error {
	if err := r.client.Del(ctx, key).Err(); err != nil {
		return handleRedisError(err, DEL)
	}
	return nil
}
