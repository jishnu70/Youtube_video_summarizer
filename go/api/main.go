package main

// go/api/main.go

import (
	"github.com/gin-gonic/gin"
	"github.com/jishnu70/Youtube_video_summarizer/api/handler"
)

var summaryHandler *handler.SummaryHandler

func init() {
	// all instances of the services and repos should be initialized here and passed to the handler

	summaryHandler = handler.NewSummaryHandler(nil) // Pass the actual VideoSummaryService instance here
}

func main() {
	app := gin.Default()
	app.Use(gin.Logger())

	app.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status": "OK",
		})
	})

	app.GET("/videos/url/:videoURL", summaryHandler.GetSummaryByVideoURL)
	app.GET("/videos/summary/summary_id/:summaryID", summaryHandler.GetVideoSummaryByIDHandler)
	app.GET("/videos/summary/id/:videoID", summaryHandler.GetVideoSummaryByVideoID)

	app.POST("/videos/summary", func(c *gin.Context) {
		// Implementation for creating a new video summary task
	})

	app.GET("/tasks/:task_id", func(c *gin.Context) {
		// Implementation for fetching the status of a specific video summary task
	})

	app.Run(":8080")
}
