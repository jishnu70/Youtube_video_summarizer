package repo

// api/internal/repo/summary.go

import (
	"context"
	"errors"
	"fmt"

	db "github.com/jishnu70/Youtube_video_summarizer/internal/db"
	domain "github.com/jishnu70/Youtube_video_summarizer/internal/domain"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"
)

type SummaryRepo struct {
	collection *mongo.Collection
}

func NewSummaryRepo(mongoDB *db.MongoDB, collectionName string) (*SummaryRepo, error) {
	if mongoDB == nil {
		return nil, domain.NewAppError(
			domain.DatabaseLayer,
			domain.CodeConnectionError,
			domain.ErrDBClientNotInitialized,
			errors.New("mongoDB client is nil"),
		)
	}
	collection := mongoDB.Collection(collectionName)
	return &SummaryRepo{
		collection: collection,
	}, nil
}

func (r *SummaryRepo) EnsureIndex(ctx context.Context) error {
	indexModel := []mongo.IndexModel{
		{Keys: bson.D{
			{Key: "video_url", Value: 1},
			{Key: "created_at", Value: -1},
		}, Options: options.Index()},
	}
	_, err := r.collection.Indexes().CreateMany(ctx, indexModel)
	if err != nil {
		return domain.NewAppError(
			domain.RepoLayer,
			domain.CodeInternalError,
			fmt.Sprintf("SummaryRepo: %s", domain.ErrDBIndexCreationFailed),
			err,
		)
	}
	return nil
}

func (r *SummaryRepo) FindByVideoURL(ctx context.Context, videoURL string) (*domain.Summary, error) {
	filter := bson.D{{Key: "video_url", Value: videoURL}}
	opts := options.FindOne().SetSort(bson.D{{Key: "created_at", Value: -1}})
	var summary db.SummaryDB
	err := r.collection.FindOne(ctx, filter, opts).Decode(&summary)
	if err != nil {
		return nil, handleRepoFindError(err, "SummaryRepo")
	}
	return summary.ToDomain(), nil
}
