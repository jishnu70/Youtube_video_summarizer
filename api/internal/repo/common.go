package repo

import (
	"errors"
	"fmt"

	domain "github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	"go.mongodb.org/mongo-driver/v2/mongo"
)

// api/internal/repo/common.go

// Common Repository error handlers

func handleRepoFindError(err error, repoName string) error {
	if mongo.IsTimeout(err) {
		return domain.NewAppError(
			domain.RepoLayer,
			domain.CodeTimeout,
			fmt.Sprintf("%s: %s", repoName, domain.ErrDBConnectionTimeout),
			err,
		)
	}
	if errors.Is(err, mongo.ErrClientDisconnected) {
		return domain.NewAppError(
			domain.RepoLayer,
			domain.CodeConnectionError,
			fmt.Sprintf("%s: %s", repoName, domain.ErrDBConnectionFailed),
			err,
		)
	}
	if errors.Is(err, mongo.ErrNoDocuments) {
		return domain.NewAppError(
			domain.RepoLayer,
			domain.CodeNotFound,
			fmt.Sprintf("%s: %s", repoName, domain.ErrDBNoDocuments),
			err,
		)
	}
	return domain.NewAppError(
		domain.RepoLayer,
		domain.CodeInternalError,
		fmt.Sprintf("%s: %s", repoName, domain.ErrDBFindFailed),
		err,
	)
}

func handleRepoInsertError(err error, repoName string) error {
	if mongo.IsDuplicateKeyError(err) {
		return domain.NewAppError(
			domain.RepoLayer,
			domain.CodeAlreadyExists,
			fmt.Sprintf("%s: %s", repoName, domain.ErrTaskAlreadyExists),
			err,
		)
	}
	if mongo.IsTimeout(err) {
		return domain.NewAppError(
			domain.RepoLayer,
			domain.CodeTimeout,
			fmt.Sprintf("%s: %s", repoName, domain.ErrDBConnectionTimeout),
			err,
		)
	}
	if errors.Is(err, mongo.ErrClientDisconnected) {
		return domain.NewAppError(
			domain.RepoLayer,
			domain.CodeConnectionError,
			fmt.Sprintf("%s: %s", repoName, domain.ErrDBConnectionFailed),
			err,
		)
	}
	return domain.NewAppError(
		domain.RepoLayer,
		domain.CodeInternalError,
		fmt.Sprintf("%s: %s", repoName, domain.ErrDBInsertFailed),
		err,
	)
}

func handleRepoDeleteError(err error, repoName string) error {
	if mongo.IsTimeout(err) {
		return domain.NewAppError(
			domain.RepoLayer,
			domain.CodeTimeout,
			fmt.Sprintf("%s: %s", repoName, domain.ErrDBConnectionTimeout),
			err,
		)
	}
	if errors.Is(err, mongo.ErrClientDisconnected) {
		return domain.NewAppError(
			domain.RepoLayer,
			domain.CodeConnectionError,
			fmt.Sprintf("%s: %s", repoName, domain.ErrDBConnectionFailed),
			err,
		)
	}
	if errors.Is(err, mongo.ErrNoDocuments) {
		return domain.NewAppError(
			domain.RepoLayer,
			domain.CodeNotFound,
			fmt.Sprintf("%s: %s", repoName, domain.ErrDBNoDocuments),
			err,
		)
	}
	if mongo.IsNetworkError(err) {
		return domain.NewAppError(
			domain.RepoLayer,
			domain.CodeConnectionError,
			fmt.Sprintf("%s: %s", repoName, domain.ErrDBConnectionFailed),
			err,
		)
	}
	return domain.NewAppError(
		domain.RepoLayer,
		domain.CodeInternalError,
		fmt.Sprintf("%s: %s", repoName, domain.ErrDBInsertFailed),
		err,
	)
}
