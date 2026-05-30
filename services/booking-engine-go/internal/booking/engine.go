package booking

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"sort"
	"strings"
	"time"
)

type ReservationRequest struct {
	ShowtimeID     string   `json:"showtime_id"`
	UserID         string   `json:"user_id"`
	SessionKey     string   `json:"session_key"`
	SeatIDs        []string `json:"seat_ids"`
	IdempotencyKey string   `json:"idempotency_key"`
}

type ReservationResponse struct {
	HoldToken string    `json:"hold_token"`
	Status    string    `json:"status"`
	ExpiresAt time.Time `json:"expires_at"`
}

type Locker interface {
	Lock(ctx context.Context, key string, owner string) error
	Unlock(ctx context.Context, key string, owner string) error
	ExpiresAt() time.Time
}

type Engine struct {
	locker Locker
}

func NewEngine(locker Locker) *Engine {
	return &Engine{locker: locker}
}

func (e *Engine) Reserve(ctx context.Context, req ReservationRequest) (ReservationResponse, error) {
	if req.ShowtimeID == "" || len(req.SeatIDs) == 0 || req.IdempotencyKey == "" {
		return ReservationResponse{}, errors.New("showtime_id, seat_ids and idempotency_key are required")
	}

	sort.Strings(req.SeatIDs)
	owner := req.IdempotencyKey
	locked := make([]string, 0, len(req.SeatIDs))
	for _, seat := range req.SeatIDs {
		key := fmt.Sprintf("seat:%s:%s", req.ShowtimeID, seat)
		if err := e.locker.Lock(ctx, key, owner); err != nil {
			for _, acquired := range locked {
				_ = e.locker.Unlock(ctx, acquired, owner)
			}
			return ReservationResponse{}, fmt.Errorf("seat unavailable: %s", seat)
		}
		locked = append(locked, key)
	}

	hash := sha256.Sum256([]byte(req.ShowtimeID + ":" + strings.Join(req.SeatIDs, ",") + ":" + req.IdempotencyKey))
	return ReservationResponse{
		HoldToken: hex.EncodeToString(hash[:])[:32],
		Status:    "HELD",
		ExpiresAt: e.locker.ExpiresAt(),
	}, nil
}

