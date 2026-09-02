package repo

// go/internal/repo/cache.go

import (
	"context"
	"time"

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

func (r *CacheRepo) Set(ctx context.Context, key string, value any, ttl int64) error {
	duration := time.Duration(ttl) * time.Second
	return r.client.Set(ctx, key, value, duration).Err()
}

func (r *CacheRepo) SetNx(ctx context.Context, key string, value any, ttl int64) (bool, error) {
	duration := time.Duration(ttl) * time.Second
	return r.client.SetNX(ctx, key, value, duration).Result()
}

func (r *CacheRepo) Get(ctx context.Context, key string) (string, error) {
	return r.client.Get(ctx, key).Result()
}

func (r *CacheRepo) GetTTl(ctx context.Context, key string) (time.Duration, error) {
	return r.client.TTL(ctx, key).Result()
}

func (r *CacheRepo) Exists(ctx context.Context, key string) (bool, error) {
	exists, err := r.client.Exists(ctx, key).Result()
	if err != nil {
		return false, err
	}
	return exists > 0, nil
}

func (r *CacheRepo) Delete(ctx context.Context, key string) error {
	return r.client.Del(ctx, key).Err()
}
