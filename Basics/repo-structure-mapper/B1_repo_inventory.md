# B1 — Repository Inventory: chai-backend

> Target: [hiteshchoudhary/chai-backend](https://github.com/hiteshchoudhary/chai-backend)  
> Analysis date: 2026-06-16  
> Agent spec: `B1_agent.md` (language-agnostic repository inventory)

---

## 1. Repository Overview

**chai-backend** is a single-module Node.js/Express REST API for a YouTube-like video hosting platform (“VideoTube”). It is the companion codebase for the [Chai Aur Code backend video series](https://github.com/hiteshchoudhary/chai-backend) and is structured as a **learning / assignment repo**: routes, models, middleware, and utilities are largely complete, while **most controller handlers are intentional TODO stubs** for students to implement (`Readme.md` lines 22–24).

**Layout:** Single package at repo root (not a monorepo). Application code lives under `src/` in conventional layers: `controllers/`, `routes/`, `models/`, `middlewares/`, `utils/`, `db/`. Static upload staging at `public/temp/`.

**Scale:** ~34 JavaScript files under `src/`; largest file `src/controllers/user.controller.js` (~495 lines, mostly implemented). No `tests/`, no CI config, no Docker files observed.

| Claim | Label | Evidence |
|-------|-------|----------|
| YouTube-like video backend | `VERIFIED` | `Readme.md` lines 11–12 |
| Assignment-style incomplete controllers | `VERIFIED` | `Readme.md` lines 22–24; `//TODO` in 8 of 9 controller files |
| Single-module layout | `VERIFIED` | One `package.json` at root; all code under `src/` |

---

## 2. Technology Stack

| Component | Value | Label | Evidence |
|-----------|-------|-------|----------|
| Language | JavaScript (ESM) | `VERIFIED` | `package.json` `"type": "module"` |
| Runtime | Node.js (version not pinned) | `INFERRED` | No `.nvmrc` / `engines` field in `package.json` |
| HTTP framework | Express 4.18.x | `VERIFIED` | `package.json` `"express": "^4.18.2"` |
| ODM / database | Mongoose 8.x → MongoDB | `VERIFIED` | `package.json` `"mongoose": "^8.0.0"`; `src/db/index.js` `mongoose.connect` |
| Auth | JWT + bcrypt + httpOnly cookies | `VERIFIED` | `jsonwebtoken`, `bcrypt`, `cookie-parser` in `package.json`; `src/middlewares/auth.middleware.js` |
| File uploads | Multer (disk) → Cloudinary | `VERIFIED` | `multer` in `package.json`; `src/middlewares/multer.middleware.js`; `src/utils/cloudinary.js` |
| Dev server | nodemon + dotenv | `VERIFIED` | `package.json` `scripts.dev` |
| Formatter | Prettier 3 | `VERIFIED` | `package.json` `devDependencies.prettier`; `.prettierrc` |
| Package manager | npm | `VERIFIED` | `package-lock.json` present |
| Entry script | `src/index.js` | `VERIFIED` | `package.json` `scripts.dev` → `src/index.js` |
| `main` field mismatch | Root `index.js` does not exist | `VERIFIED` | `package.json` `"main": "index.js"`; no `index.js` at repo root in file tree |

---

## 3. Module Inventory

Logical modules map to `src/routes/*.routes.js` + matching controller/model files. There is **no separate service or repository layer** — controllers are expected to call Mongoose models directly (`INFERRED` from directory structure: no `services/` or `repositories/` folder).

| Module | Responsibility | Key internal deps | Entry point / mount | Label |
|--------|----------------|-------------------|---------------------|-------|
| **Bootstrap** | Load env, connect DB, start HTTP server | `src/db/index.js`, `src/app.js` | `src/index.js` | `VERIFIED` |
| **App shell** | Express middleware + route mounting | All `src/routes/*` | `src/app.js` exports `{ app }` | `VERIFIED` |
| **Healthcheck** | Liveness probe | `healthcheck.controller.js` | `GET /api/v1/healthcheck/` | `VERIFIED` |
| **Users / Auth** | Register, login, JWT, profile, avatar/cover | `User` model, `verifyJWT`, `upload`, Cloudinary | `app.use("/api/v1/users", …)` | `VERIFIED` |
| **Videos** | CRUD, publish toggle, upload | `Video` model, `upload`, `verifyJWT` | `/api/v1/videos` | `VERIFIED` |
| **Comments** | Video comments CRUD | `Comment` model | `/api/v1/comments` | `VERIFIED` |
| **Likes** | Toggle likes on video/comment/tweet | `Like` model | `/api/v1/likes` | `VERIFIED` |
| **Tweets** | Channel tweets CRUD | `Tweet` model | `/api/v1/tweets` | `VERIFIED` |
| **Subscriptions** | Subscribe/unsubscribe, list subs | `Subscription` model | `/api/v1/subscriptions` | `VERIFIED` |
| **Playlists** | Playlist CRUD, add/remove videos | `Playlist` model | `/api/v1/playlist` | `VERIFIED` |
| **Dashboard** | Channel stats and video list | Aggregations over `Video`, `User`, etc. | `/api/v1/dashboard` | `VERIFIED` |

---

## 4. Service Inventory

**No dedicated `*Service` / use-case layer exists.**

| Name | Path | Purpose | Key deps | Label |
|------|------|---------|----------|-------|
| — | — | Business logic lives in controllers and Mongoose model methods | — | `VERIFIED` (absence of `src/services/`) |

**Model-level “services” (domain behavior on schemas):**

| Name | Path | Purpose | Key deps | Label |
|------|------|---------|----------|-------|
| `isPasswordCorrect` | `src/models/user.model.js` | bcrypt password compare | `bcrypt` | `VERIFIED` |
| `generateAccessToken` | `src/models/user.model.js` | JWT access token | `jsonwebtoken`, `ACCESS_TOKEN_*` env | `VERIFIED` |
| `generateRefreshToken` | `src/models/user.model.js` | JWT refresh token | `jsonwebtoken`, `REFRESH_TOKEN_*` env | `VERIFIED` |
| pre-save password hash | `src/models/user.model.js` | Hash password on save | `bcrypt` | `VERIFIED` |

**Long tail:** 0 `*Service` classes; 4 model methods/hooks on `User` only (others are plain schemas).

---

## 5. Controller / API Handler Inventory

Pattern: `asyncHandler`-wrapped functions in `src/controllers/*.controller.js`, wired in `src/routes/*.routes.js`, mounted from `src/app.js`.

### Implementation status

| Controller | Path | Handlers | Status | Label |
|------------|------|----------|--------|-------|
| `user.controller.js` | `src/controllers/user.controller.js` | 11 exported handlers | **Mostly complete** — register/login/logout, refresh, password, profile, avatar/cover, channel profile, watch history; 2 optional Cloudinary cleanup TODOs | `VERIFIED` |
| `healthcheck.controller.js` | `src/controllers/healthcheck.controller.js` | `healthcheck` | **Stub** — TODO only | `VERIFIED` |
| `video.controller.js` | `src/controllers/video.controller.js` | 6 handlers | **Stub** — 5 explicit TODOs | `VERIFIED` |
| `comment.controller.js` | `src/controllers/comment.controller.js` | 4 handlers | **Stub** — all TODO | `VERIFIED` |
| `like.controller.js` | `src/controllers/like.controller.js` | 4 handlers | **Stub** — all TODO | `VERIFIED` |
| `tweet.controller.js` | `src/controllers/tweet.controller.js` | 4 handlers | **Stub** — all TODO | `VERIFIED` |
| `subscription.controller.js` | `src/controllers/subscription.controller.js` | 3 handlers | **Stub** — 1 TODO; others parse params only | `VERIFIED` |
| `playlist.controller.js` | `src/controllers/playlist.controller.js` | 7 handlers | **Stub** — 6 TODOs | `VERIFIED` |
| `dashboard.controller.js` | `src/controllers/dashboard.controller.js` | 2 handlers | **Stub** — both TODO | `VERIFIED` |

### User controller handlers (reference implementation)

| Handler | Purpose | Label | Evidence |
|---------|---------|-------|----------|
| `registerUser` | Create user, Multer → Cloudinary avatar/cover | `VERIFIED` | `user.controller.js` line 27; `ApiResponse` line 96 |
| `loginUser` | Credentials → tokens in cookies | `VERIFIED` | `user.controller.js` line 101 |
| `logoutUser` | Clear cookies, clear refresh token | `VERIFIED` | `user.controller.js` line 161 |
| `refreshAccessToken` | Issue new access token from refresh | `VERIFIED` | `user.controller.js` line 186 |
| `changeCurrentPassword` | Update password | `VERIFIED` | `user.controller.js` line 251 area |
| `getCurrentUser` | Return `req.user` | `VERIFIED` | export list line 487+ |
| `updateAccountDetails` | Patch name/email | `VERIFIED` | `ApiResponse` line 286 |
| `updateUserAvatar` / `updateUserCoverImage` | Cloudinary upload | `VERIFIED` | lines 298, 332 |
| `getUserChannelProfile` | Aggregation by username | `VERIFIED` | `ApiResponse` line 425 |
| `getWatchHistory` | Populate watch history | `VERIFIED` | `ApiResponse` line 475 |

### Route map (all mounts)

Base URL prefix: `/api/v1` (`src/app.js` lines 30–38).

| Mount | Methods & paths | Controller handlers | JWT | Label |
|-------|-----------------|---------------------|-----|-------|
| `/healthcheck` | `GET /` | `healthcheck` | No | `VERIFIED` |
| `/users` | `POST /register`, `/login`, `/refresh-token`; secured: `/logout`, `/change-password`, `/current-user`, `/update-account`, `/avatar`, `/cover-image`, `/c/:username`, `/history` | user handlers | Per-route | `VERIFIED` |
| `/tweets` | `POST /`, `GET /user/:userId`, `PATCH\|DELETE /:tweetId` | tweet handlers | Router-wide | `VERIFIED` |
| `/subscriptions` | `GET\|POST /c/:channelId`, `GET /u/:subscriberId` | subscription handlers | Router-wide | `VERIFIED` |
| `/videos` | `GET\|POST /`, `GET\|DELETE\|PATCH /:videoId`, `PATCH /toggle/publish/:videoId` | video handlers | Router-wide | `VERIFIED` |
| `/comments` | `GET\|POST /:videoId`, `DELETE\|PATCH /c/:commentId` | comment handlers | Router-wide | `VERIFIED` |
| `/likes` | `POST /toggle/v/:videoId`, `/toggle/c/:commentId`, `/toggle/t/:tweetId`; `GET /videos` | like handlers | Router-wide | `VERIFIED` |
| `/playlist` | `POST /`, `GET\|PATCH\|DELETE /:playlistId`, add/remove video, `GET /user/:userId` | playlist handlers | Router-wide | `VERIFIED` |
| `/dashboard` | `GET /stats`, `GET /videos` | dashboard handlers | Router-wide | `VERIFIED` |

**Known wiring issue:** `subscription.routes.js` defines `GET /u/:subscriberId` but `subscription.controller.js` reads `req.params.channelId` for `getUserChannelSubscribers` (`INFERRED` mismatch — confirm when implementing).

---

## 6. Repository / Data-Access Inventory

**No repository/DAO layer.** Data access is Mongoose models in `src/models/`.

| Model | Path | Collection purpose | Notable fields / plugins | Label |
|-------|------|-------------------|--------------------------|-------|
| `User` | `src/models/user.model.js` | Accounts & channels | `username`, `email`, `avatar`, `coverImage`, `watchHistory[]`, `refreshToken`; bcrypt + JWT methods | `VERIFIED` |
| `Video` | `src/models/video.model.js` | Hosted videos | `videoFile`, `thumbnail`, `title`, `description`, `duration`, `views`, `isPublished`, `owner`; aggregate paginate plugin | `VERIFIED` |
| `Comment` | `src/models/comment.model.js` | Video comments | `content`, `video`, `owner`; aggregate paginate plugin | `VERIFIED` |
| `Like` | `src/models/like.model.js` | Polymorphic likes | optional `video` / `comment` / `tweet`, `likedBy` | `VERIFIED` |
| `Playlist` | `src/models/playlist.model.js` | User playlists | `name`, `description`, `videos[]`, `owner` | `VERIFIED` |
| `Subscription` | `src/models/subscription.model.js` | Channel subscriptions | `subscriber`, `channel` (both `User` refs) | `VERIFIED` |
| `Tweet` | `src/models/tweet.model.js` | Channel tweets | `content`, `owner` | `VERIFIED` |

**DB connection:**

| Name | Path | Purpose | Label | Evidence |
|------|------|---------|-------|----------|
| `connectDB` | `src/db/index.js` | `mongoose.connect(\`${MONGODB_URI}/${DB_NAME}\`)` | `VERIFIED` | lines 5–15 |
| `DB_NAME` | `src/constants.js` | Database name `"videotube"` | `VERIFIED` | `export const DB_NAME = "videotube"` |

---

## 7. Utility / Shared-Library Inventory

| Name | Path | Purpose | Key deps | Label |
|------|------|---------|----------|-------|
| `ApiError` | `src/utils/ApiError.js` | HTTP error type (`statusCode`, `errors[]`) | — | `VERIFIED` |
| `ApiResponse` | `src/utils/ApiResponse.js` | Standard success envelope | — | `VERIFIED` |
| `asyncHandler` | `src/utils/asyncHandler.js` | Wrap async route handlers → `next(err)` | — | `VERIFIED` |
| `uploadOnCloudinary` | `src/utils/cloudinary.js` | Upload local file, delete temp, return Cloudinary response | `cloudinary`, `fs` | `VERIFIED` |
| `verifyJWT` | `src/middlewares/auth.middleware.js` | Parse cookie/Bearer token, attach `req.user` | `jwt`, `User` | `VERIFIED` |
| `upload` | `src/middlewares/multer.middleware.js` | Disk storage to `./public/temp` | `multer` | `VERIFIED` |

**Long tail:** 4 utils + 2 middleware files; no other helper directories.

---

## 8. Infrastructure Components

| Component | Status | Label | Evidence |
|-----------|--------|-------|----------|
| **MongoDB** | Primary datastore | `VERIFIED` | `MONGODB_URI` in `.env.sample`; `mongoose.connect` in `src/db/index.js` |
| **Cloudinary** | Media CDN for avatars, covers, videos, thumbnails | `VERIFIED` | `CLOUDINARY_*` in `.env.sample`; `src/utils/cloudinary.js` |
| **Local disk** | Temporary Multer staging | `VERIFIED` | `public/temp/`; `multer.middleware.js` `destination: "./public/temp"` |
| **Queues / message brokers** | NOT FOUND IN REPOSITORY | `VERIFIED` | No redis/kafka/bull imports |
| **Cache (Redis, etc.)** | NOT FOUND IN REPOSITORY | `VERIFIED` | No cache client in `package.json` |
| **Cron / background workers** | NOT FOUND IN REPOSITORY | `VERIFIED` | No scheduler deps or job files |
| **Feature flags** | NOT FOUND IN REPOSITORY | `VERIFIED` | No flag SDK or config |
| **Docker / K8s** | NOT FOUND IN REPOSITORY | `VERIFIED` | No `Dockerfile`, `docker-compose`, `k8s/` |
| **CI/CD** | NOT FOUND IN REPOSITORY | `VERIFIED` | No `.github/workflows`, `.gitlab-ci.yml` |
| **Global error middleware** | NOT FOUND IN REPOSITORY | `VERIFIED` | `src/app.js` ends at route mounts (line 42); no `(err, req, res, next)` handler |

### Environment configuration (`.env.sample`)

| Variable | Purpose | Label |
|----------|---------|-------|
| `PORT` | HTTP port (default 8000 in code) | `VERIFIED` |
| `MONGODB_URI` | MongoDB connection string | `VERIFIED` |
| `CORS_ORIGIN` | CORS allowed origin | `VERIFIED` |
| `ACCESS_TOKEN_SECRET` / `ACCESS_TOKEN_EXPIRY` | JWT access token | `VERIFIED` |
| `REFRESH_TOKEN_SECRET` / `REFRESH_TOKEN_EXPIRY` | JWT refresh token | `VERIFIED` |
| `CLOUDINARY_CLOUD_NAME` / `API_KEY` / `API_SECRET` | Cloudinary credentials | `VERIFIED` |

---

## 9. External Dependencies

| Package | Version (manifest) | Used for | Label |
|---------|------------------|----------|-------|
| `express` | ^4.18.2 | HTTP server, routing | `VERIFIED` |
| `mongoose` | ^8.0.0 | MongoDB ODM | `VERIFIED` |
| `mongoose-aggregate-paginate-v2` | ^1.0.6 | Paginated aggregations on `Video`, `Comment` | `VERIFIED` |
| `bcrypt` | ^5.1.1 | Password hashing | `VERIFIED` |
| `jsonwebtoken` | ^9.0.2 | Access/refresh tokens | `VERIFIED` |
| `cookie-parser` | ^1.4.6 | httpOnly cookie auth | `VERIFIED` |
| `cors` | ^2.8.5 | Cross-origin requests | `VERIFIED` |
| `dotenv` | ^16.3.1 | Environment variables | `VERIFIED` |
| `multer` | ^1.4.5-lts.1 | Multipart uploads | `VERIFIED` |
| `cloudinary` | ^1.41.0 | Cloud media storage | `VERIFIED` |
| `nodemon` | ^3.0.1 (dev) | Hot reload | `VERIFIED` |
| `prettier` | ^3.0.3 (dev) | Code formatting | `VERIFIED` |

---

## 10. New Engineer Summary

### What this system is

A **MongoDB-backed Express API** for a video platform. The **intended learning path** is to study the finished **user/auth flow**, then implement the remaining **controller TODOs** while using existing routes, models, and middleware.

### Start here (reading order)

1. **`Readme.md`** — product scope and contribution rules (finish all controllers).
2. **`package.json`** + **`.env.sample`** — stack and required secrets.
3. **`src/index.js`** — bootstrap: `dotenv` → `connectDB()` → `app.listen`.
4. **`src/app.js`** — global middleware and `/api/v1/*` route mounts.
5. **`src/routes/user.routes.js`** + **`src/controllers/user.controller.js`** — reference implementation (auth, uploads, aggregations).
6. **`src/middlewares/auth.middleware.js`** — how `req.user` is populated.
7. **`src/models/user.model.js`** — password hashing and token generation.
8. Pick one stub domain (e.g. **`video.routes.js`** → **`video.controller.js`** → **`video.model.js`**) and implement end-to-end.

### One full flow (implemented): User registration

```text
POST /api/v1/users/register (multipart)
  → multer.fields(avatar, coverImage)     [user.routes.js]
  → registerUser                          [user.controller.js]
      → uploadOnCloudinary (temp files)   [utils/cloudinary.js]
      → User.create(...)
  → 200 ApiResponse { user }
```

### Architecture diagram

```text
HTTP client
    │
    ▼
src/index.js          dotenv + connectDB + listen
    │
    ▼
src/app.js            cors, json, static, cookies
    │
    ▼
src/routes/*.js       verifyJWT (most routers) + multer (upload routes)
    │
    ▼
src/controllers/*.js  asyncHandler-wrapped handlers  [mostly TODO except user]
    │
    ▼
src/models/*.js       Mongoose schemas (+ User methods)
    │
    ▼
MongoDB (videotube)   + Cloudinary (media URLs)
```

---

## Files Analyzed

| Category | Count / paths |
|----------|----------------|
| Root manifests & docs | `package.json`, `package-lock.json`, `.env.sample`, `Readme.md`, `.prettierrc`, `.gitignore` |
| `src/` JavaScript | 34 files (9 controllers, 9 routes, 7 models, 2 middlewares, 4 utils, `app.js`, `index.js`, `constants.js`, `db/index.js`) |
| **Total inspected** | **~40 non-git files** |

---

## Open Questions

| Item | Notes |
|------|-------|
| Node.js version | No `engines` field — confirm with team/local LTS |
| Global error handler | `ApiError` thrown in middleware may not serialize without added Express error middleware |
| `email.lowecase` typo | `src/models/user.model.js` line 19 — likely meant `lowercase` |
| Subscription route param mismatch | Route `:subscriberId` vs controller `channelId` |
| Reply-to-comment feature | Mentioned in README (`Readme.md` line 12) but no separate Reply model — `INFERRED` may be nested comments or not yet modeled |
| Test strategy | No test framework in repo — assignment repos may omit tests by design |
