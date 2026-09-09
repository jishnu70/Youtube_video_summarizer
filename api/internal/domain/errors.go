package domain

import (
	"fmt"
)

// api/internal/domain/errors.go

type ErrorLayer string

const (
	ConfigLayer   ErrorLayer = "CONFIG_LAYER"
	DatabaseLayer ErrorLayer = "DATABASE_LAYER"
	CacheLayer    ErrorLayer = "CACHE_LAYER"
	RepoLayer     ErrorLayer = "REPO_LAYER"
	ServiceLayer  ErrorLayer = "SERVICE_LAYER"
)

type ErrorCode string

const (
	CodeNotFound            ErrorCode = "NOT_FOUND"
	CodeInvalidInput        ErrorCode = "INVALID_INPUT"
	CodeConnectionError     ErrorCode = "CONNECTION_ERROR"
	CodeTimeout             ErrorCode = "TIMEOUT"
	CodeInternalError       ErrorCode = "INTERNAL_ERROR"
	CodeAlreadyExists       ErrorCode = "ALREADY_EXISTS"
	CodeInsufficientData    ErrorCode = "INSUFFICIENT_DATA"
	CodeInternalServerError ErrorCode = "INTERNAL_SERVER_ERROR"
)

type AppError struct {
	ErrLayer ErrorLayer
	ErrCode  ErrorCode
	Message  string
	Err      error
}

func (e AppError) Error() string {
	if e.Err != nil {
		return fmt.Sprintf("[%s][%s] %s: %v", e.ErrLayer, e.ErrCode, e.Message, e.Err)
	}
	return fmt.Sprintf("[%s][%s] %s", e.ErrLayer, e.ErrCode, e.Message)
}

func (e AppError) Unwrap() error {
	return e.Err
}

func NewAppError(layer ErrorLayer, code ErrorCode, message string, err error) error {
	return &AppError{
		ErrLayer: layer,
		ErrCode:  code,
		Message:  message,
		Err:      err,
	}
}

// Defining all config errors
const (
	ErrConfigFileNotFound = "config file not found"
	ErrConfigMissingField = "missing required configuration field"
	ErrConfigInvalidValue = "invalid configuration value"
)

// Defining all DB errors
const (
	ErrDBClientNotInitialized = "database client is nil"
	ErrDBConnectionFailed     = "failed to connect to database"
	ErrDBConnectionTimeout    = "database connection timed out"
	ErrDBDisconnectFailed     = "failed to disconnect from database"
	ErrDBCollectionNotFound   = "database collection not found"
	ErrDBPingFailed           = "failed to ping database"
	ErrDBIndexCreationFailed  = "failed to create index in database"
	ErrDBInsertFailed         = "failed to insert document into database"
	ErrDBFindFailed           = "failed to find document in database"
	ErrDBNoDocuments          = "no documents found in database"
)

// Defining all cache errors
const (
	ErrCacheClientNotInitialized = "cache client is nil"
	ErrCacheConnectionFailed     = "failed to connect to cache"
	ErrCacheConnectionTimeout    = "cache connection timed out"
	ErrCachePingFailed           = "failed to ping cache"
	ErrCacheDisconnectFailed     = "failed to disconnect from cache"
	ErrCacheKeyNotFound          = "cache key not found"
	ErrCacheSetFailed            = "failed to set cache value"
	ErrCacheKeyAlreadyExists     = "cache key already exists"
	ErrCacheGetFailed            = "failed to get cache value"
	ErrCacheDeleteFailed         = "failed to delete cache value"
)

// Defining all Repo errors
const (
	ErrSummaryDBNotFound = "summary not found in database"
	ErrTaskDBNotFound    = "task not found in database"

	ErrSummaryCacheNotFound          = "summary not found in cache"
	ErrTaskCacheNotFound             = "task not found in cache"
	ErrVideoURLToTaskIDCacheNotFound = "video URL to task ID mapping not found in cache"
)

// Defining all Service errors
const (
	ErrVideoURLEmpty     = "video URL is empty"
	ErrTaskIDEmpty       = "task ID is empty"
	ErrInvalidVideoURL   = "invalid video URL"
	ErrTaskAlreadyExists = "task already exists for the given video URL"
	ErrInvalidTaskID     = "invalid task ID"
)
