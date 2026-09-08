package config

// api/internal/config/config.go

import (
	"errors"
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

func LoadConfig() *Config {
	config := &Config{}
	config.LoadMongoConfig()
	config.loadRedisConfig()

	return config
}

func (c *Config) LoadMongoConfig() {
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
			panic(errors.New("DB:" + domain.ErrConfigMissingField.Error() + ": " + env.key))
		}
		*env.value = value
	}
}

func (c *Config) loadRedisConfig() {
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
			panic(errors.New("Redis" + domain.ErrConfigMissingField.Error() + ": " + env.key))
		}
		*env.value = value
	}

	// Handle REDIS_PORT separately since it needs to be converted to an integer
	portStr := os.Getenv("REDIS_PORT")
	if portStr == "" {
		panic(errors.New("Redis" + domain.ErrConfigMissingField.Error() + ": REDIS_PORT"))
	}

	port, err := strconv.Atoi(portStr)
	if err != nil {
		panic(errors.New("Redis: invalid REDIS_PORT value: " + portStr))
	}
	c.RedisPort = port

	c.RedisAddr = fmt.Sprintf("%s:%d", c.RedisHost, c.RedisPort)
}
