package repo

// api/internal/repo/task.go

import (
	"context"
	"errors"
	"fmt"

	db "github.com/jishnu70/Youtube_video_summarizer/internal/db"
	"github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"
)

type TaskRepo struct {
	// Implement the TaskRepo struct and its methods here
	collection *mongo.Collection
}

func NewTaskRepo(mongoDB *db.MongoDB, collectionName string) (*TaskRepo, error) {
	if mongoDB == nil {
		return nil, domain.NewAppError(
			domain.DatabaseLayer,
			domain.CodeConnectionError,
			domain.ErrDBClientNotInitialized,
			errors.New("mongoDB client is nil"),
		)
	}
	collection := mongoDB.Collection(collectionName)
	return &TaskRepo{
		collection: collection,
	}, nil
}

// Implement the methods for TaskRepo here
func (r *TaskRepo) EnsureIndex(ctx context.Context) error {
	// Implement the logic to create indexes for the task collection
	indexModel := []mongo.IndexModel{
		{Keys: bson.D{{Key: "video_url", Value: 1}}, Options: options.Index().SetUnique(true)},
	}
	_, err := r.collection.Indexes().CreateMany(ctx, indexModel)
	if err != nil {
		return domain.NewAppError(
			domain.RepoLayer,
			domain.CodeInternalError,
			fmt.Sprintf("TaskRepo: %s", domain.ErrDBIndexCreationFailed),
			err,
		)
	}
	return nil
}

func (r *TaskRepo) Insert(ctx context.Context, task *domain.BackgroundTaskStatus) (*domain.BackgroundTaskStatus, error) {
	if task == nil {
		return nil, errors.New("task is nil")
	}
	dbTask := db.BackgroundTaskStatusDB{
		ID:        bson.NewObjectID(),
		VideoURL:  task.VideoURL,
		Message:   task.Message,
		Status:    task.Status,
		CreatedAt: task.CreatedAt,
		UpdatedAt: task.UpdatedAt,
	}
	_, err := r.collection.InsertOne(ctx, dbTask)
	if err != nil {
		return nil, handleRepoInsertError(err, "TaskRepo")
	}
	return dbTask.ToDomain(), nil
}

func (r *TaskRepo) FindByID(ctx context.Context, id string) (*domain.BackgroundTaskStatus, error) {
	bsonID, err := bson.ObjectIDFromHex(id)
	if err != nil {
		return nil, domain.NewAppError(
			domain.RepoLayer,
			domain.CodeInvalidInput,
			fmt.Sprintf("TaskRepo: %s", domain.ErrInvalidTaskID),
			err,
		)
	}
	var dbTask db.BackgroundTaskStatusDB
	err = r.collection.FindOne(ctx, bson.M{"_id": bsonID}).Decode(&dbTask)
	if err != nil {
		return nil, handleRepoFindError(err, "TaskRepo")
	}
	return dbTask.ToDomain(), nil
}

func (r *TaskRepo) FindByVideoURL(ctx context.Context, videoURL string) (*domain.BackgroundTaskStatus, error) {
	var dbTask db.BackgroundTaskStatusDB
	err := r.collection.FindOne(ctx, bson.M{"video_url": videoURL}).Decode(&dbTask)
	if err != nil {
		return nil, handleRepoFindError(err, "TaskRepo")
	}
	return dbTask.ToDomain(), nil
}
