package main

// api/requests/main.go

import (
	"errors"
	"log"
	"log/slog"
	"net/http"
	"runtime/debug"

	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"

	config "github.com/jishnu70/Youtube_video_summarizer/internal/config"
	db "github.com/jishnu70/Youtube_video_summarizer/internal/db"
	"github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	repo "github.com/jishnu70/Youtube_video_summarizer/internal/repo"
	service "github.com/jishnu70/Youtube_video_summarizer/internal/service"
	handler "github.com/jishnu70/Youtube_video_summarizer/requests/handler"
)

func initializeClients(c *config.Config) (*db.MongoDB, *redis.Client) {
	mongoClient, err := db.New(c.MongoURI, c.MongoDatabase)
	if err != nil {
		log.Fatalf("failed to connect to MongoDB: %v", err)
	}

	redisClient := redis.NewClient(&redis.Options{
		Addr:     c.RedisAddr,
		Password: c.RedisPassword,
	})

	return mongoClient, redisClient
}

func initializeRepositories(mongoClient *db.MongoDB, redisClient *redis.Client, c *config.Config) (*repo.SummaryRepo, *repo.TaskRepo, *repo.CacheRepo) {
	summaryRepo, err := repo.NewSummaryRepo(mongoClient, c.SummaryCollection)
	if err != nil {
		log.Fatalf("failed to create summary repo: %v", err)
	}
	taskRepo, err := repo.NewTaskRepo(mongoClient, c.TaskCollection)
	if err != nil {
		log.Fatalf("failed to create task repo: %v", err)
	}
	cacheRepo := repo.NewCacheRepo(redisClient)

	return summaryRepo, taskRepo, cacheRepo
}

func initializeServices(summaryRepo *repo.SummaryRepo, taskRepo *repo.TaskRepo, cacheRepo *repo.CacheRepo) (*service.SummaryService, *service.TaskService, *service.CacheService) {
	cacheService, err := service.NewCacheService(cacheRepo)
	if err != nil {
		log.Fatalf("failed to create cache service: %v", err)
	}

	summaryService, err := service.NewSummaryService(summaryRepo, cacheService)
	if err != nil {
		log.Fatalf("failed to create summary service: %v", err)
	}

	taskService, err := service.NewTaskService(taskRepo, cacheService)
	if err != nil {
		log.Fatalf("failed to create task service: %v", err)
	}

	return summaryService, taskService, cacheService
}

func initializeRequestHandler(summaryService *service.SummaryService, taskService *service.TaskService) *handler.RequestHandler {
	requestHandler := handler.NewRequestHandler(summaryService, taskService)
	return requestHandler
}

func main() {
	config, err := config.LoadConfig()
	if err != nil {
		log.Fatalf("failed to load config: %v", err)
	}

	mongoClient, redisClient := initializeClients(config)
	summaryRepo, taskRepo, cacheRepo := initializeRepositories(mongoClient, redisClient, config)
	summaryService, taskService, _ := initializeServices(summaryRepo, taskRepo, cacheRepo)
	requestHandler := initializeRequestHandler(summaryService, taskService)

	app := gin.Default()
	app.Use(gin.Recovery())
	app.Use(gin.Logger())
	app.Use(ErrorHandlingMiddleware())

	app.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status": "OK",
		})
	})

	app.GET("/summary/", requestHandler.GetSummary)
	app.GET("/task/", requestHandler.GetTaskStatus)

	log.Fatal(app.Run(":8080"))
}

func ErrorHandlingMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			if err := recover(); err != nil {
				slog.Error("CRITICAL PANIC RECOVERED",
					"error", err,
					"stack", string(debug.Stack()),
					"path", c.Request.URL.Path,
				)

				c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{
					"code":    "INTERNAL_SERVER_ERROR",
					"message": "An unexpected error occurred.",
				})
			}
		}()

		c.Next()

		if len(c.Errors) > 0 {
			err := c.Errors.Last().Err

			switch {
			case errors.Is(err, domain.ErrVideoURLEmpty),
				errors.Is(err, domain.ErrTaskIDEmpty),
				errors.Is(err, domain.ErrDBInvalidObjectID):
				slog.Warn("Client validation error", "error", err.Error(), "path", c.Request.URL.Path)
				c.AbortWithStatusJSON(http.StatusBadRequest, gin.H{
					"code":    "BAD_REQUEST",
					"message": err.Error(), // Safe to show: "video URL is empty", etc.
				})
			case errors.Is(err, domain.ErrSummaryNotFound),
				errors.Is(err, domain.ErrTaskNotFound),
				errors.Is(err, domain.ErrTaskIDNotFound):
				slog.Info("Resource not found", "error", err.Error(), "path", c.Request.URL.Path)
				c.AbortWithStatusJSON(http.StatusNotFound, gin.H{
					"code":    "NOT_FOUND",
					"message": err.Error(), // Safe to show: "summary not found", etc.
				})
			default:
				slog.Error("Unhandled infrastructure or system error",
					"error", err.Error(),
					"path", c.Request.URL.Path,
				)

				// Mask the error completely from the client to prevent security leaks
				c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{
					"code":    "INTERNAL_SERVER_ERROR",
					"message": "An unexpected server error occurred. Please try again later.",
				})
			}
		}
	}
}
