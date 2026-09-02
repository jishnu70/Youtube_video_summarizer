package repo

// go/internal/repo/task.go

import (
	"context"
	"errors"
	"time"

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
		return nil, errors.New("mongodb client is not initialized")
	}
	collection, err := mongoDB.Collection(collectionName)
	if err != nil {
		return nil, err
	}
	return &TaskRepo{
		collection: collection,
	}, nil
}

// Implement the methods for TaskRepo here
func (r *TaskRepo) EnsureIndex(ctx context.Context) error {
	// Implement the logic to create indexes for the task collection
	indexModel := []mongo.IndexModel{
		{Keys: bson.D{{Key: "video_url", Value: 1}}, Options: options.Index()},
	}
	_, err := r.collection.Indexes().CreateMany(ctx, indexModel)
	if err != nil {
		return err
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
		Status:    task.Status,
		CreatedAt: task.CreatedAt,
		UpdatedAt: task.UpdatedAt,
	}
	_, err := r.collection.InsertOne(ctx, dbTask)
	if err != nil {
		return nil, err
	}
	return dbTask.ToDomain(), nil
}

func (r *TaskRepo) FindByID(ctx context.Context, id string) (*domain.BackgroundTaskStatus, error) {
	bsonID, err := bson.ObjectIDFromHex(id)
	if err != nil {
		return nil, errors.New("invalid ObjectID format")
	}
	var dbTask db.BackgroundTaskStatusDB
	err = r.collection.FindOne(ctx, bson.M{"_id": bsonID}).Decode(&dbTask)
	if err != nil {
		return nil, domain.ErrTaskNotFound
	}
	return dbTask.ToDomain(), nil
}

func (r *TaskRepo) FindByVideoURL(ctx context.Context, videoURL string) (*domain.BackgroundTaskStatus, error) {
	var dbTask db.BackgroundTaskStatusDB
	err := r.collection.FindOne(ctx, bson.M{"video_url": videoURL}).Decode(&dbTask)
	if err != nil {
		return nil, domain.ErrTaskNotFound
	}
	return dbTask.ToDomain(), nil
}

func (r *TaskRepo) Update(ctx context.Context, task *domain.BackgroundTaskStatus, updateFields map[string]any) error {
	if task == nil {
		return errors.New("task is nil")
	}
	if len(updateFields) == 0 {
		return errors.New("no fields to update")
	}
	bsonID, err := bson.ObjectIDFromHex(task.ID)
	if err != nil {
		return errors.New("invalid ObjectID format")
	}
	bsonUpdate := bson.D{}
	for k, v := range updateFields {
		bsonUpdate = append(bsonUpdate, bson.E{Key: k, Value: v})
	}
	bsonUpdate = append(bsonUpdate, bson.E{Key: "updated_at", Value: time.Now().UTC()})
	result, err := r.collection.UpdateOne(ctx, bson.M{"_id": bsonID}, bson.M{"$set": bsonUpdate})
	if err != nil {
		return err
	}
	if result.MatchedCount == 0 {
		return domain.ErrTaskNotFound
	}
	return nil
}

func (r *TaskRepo) Delete(ctx context.Context, id string) error {
	bsonID, err := bson.ObjectIDFromHex(id)
	if err != nil {
		return errors.New("invalid ObjectID format")
	}
	result, err := r.collection.DeleteOne(ctx, bson.M{"_id": bsonID})
	if err != nil {
		return err
	}
	if result.DeletedCount == 0 {
		return domain.ErrTaskNotFound
	}
	return nil
}
