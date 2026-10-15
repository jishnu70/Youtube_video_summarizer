package config

// api/internal/config/config.go

import (
	"fmt"
	"os"
	"strconv"

	"github.com/jishnu70/Youtube_video_summarizer/internal/domain"
)

type Config struct {

	// mongo related configuration
	MongoURI      string
	MongoDatabase string

	// collection names
	TaskCollection    string
	SummaryCollection string

	// redis related configuration
	RedisHost     string
	RedisPort     int
	RedisAddr     string
	RedisPassword string
}

func LoadConfig() (*Config, error) {
	config := &Config{}
	if err := config.LoadMongoConfig(); err != nil {
		return nil, err
	}
	if err := config.loadRedisConfig(); err != nil {
		return nil, err
	}

	return config, nil
}

func (c *Config) LoadMongoConfig() error {
	envMapping := []struct {
		key   string
		value *string
	}{
		{"MONGO_URI", &c.MongoURI},
		{"MONGO_DATABASE", &c.MongoDatabase},
		{"TASK_COLLECTION", &c.TaskCollection},
		{"SUMMARY_COLLECTION", &c.SummaryCollection},
	}

	for _, env := range envMapping {
		value := os.Getenv(env.key)
		if value == "" {
			return domain.NewAppError(
				domain.ConfigLayer,
				domain.CodeInvalidInput,
				fmt.Sprintf("%s: %s", domain.ErrConfigMissingField, env.key),
				nil,
			)
		}
		*env.value = value
	}
	return nil
}

func (c *Config) loadRedisConfig() error {
	envMapping := []struct {
		key   string
		value *string
	}{
		{"REDIS_HOST", &c.RedisHost},
		{"REDIS_PASSWORD", &c.RedisPassword},
	}

	for _, env := range envMapping {
		value := os.Getenv(env.key)
		if value == "" {
			return domain.NewAppError(
				domain.ConfigLayer,
				domain.CodeInvalidInput,
				fmt.Sprintf("%s: %s", domain.ErrConfigMissingField, env.key),
				nil,
			)
		}
		*env.value = value
	}

	// Handle REDIS_PORT separately since it needs to be converted to an integer
	portStr := os.Getenv("REDIS_PORT")
	if portStr == "" {
		return domain.NewAppError(
			domain.ConfigLayer,
			domain.CodeInvalidInput,
			fmt.Sprintf("%s: %s", domain.ErrConfigMissingField, "REDIS_PORT"),
			nil,
		)
	}

	port, err := strconv.Atoi(portStr)
	if err != nil {
		return domain.NewAppError(
			domain.ConfigLayer,
			domain.CodeInvalidInput,
			fmt.Sprintf("%s: %s", domain.ErrConfigInvalidValue, "REDIS_PORT"),
			err,
		)
	}
	c.RedisPort = port

	c.RedisAddr = fmt.Sprintf("%s:%d", c.RedisHost, c.RedisPort)

	return nil
}
