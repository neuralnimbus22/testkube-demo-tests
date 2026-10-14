# Android smoke tests with Maestro on Kubernetes

Two Maestro smoke flows for the Wikipedia Android app, run by a Testkube workflow.

## What is here

| Path | What it is |
|---|---|
| `apps/wikipedia-sample.apk` | Sample app under test (Wikipedia 2.7, `org.wikipedia`). The workflow downloads it by URL, the same way it would download a build from CI. |
| `maestro/common/skip-onboarding.yaml` | Shared step. Starts the app from a clean state and skips the welcome screens. |
| `maestro/01-app-opens-and-shows-feed.yaml` | The app opens and the Explore feed loads live content. |
| `maestro/02-search-and-open-article.yaml` | Search returns results and an article opens. |
| `testkube/android-maestro-smoke.yaml` | The Testkube workflow that runs the flows. |

## How a run works

1. Testkube starts an Android emulator in its own pod. The pod uses the node's KVM device, so it runs privileged.
2. Testkube waits until Android has finished booting.
3. The test pod clones this folder, installs the Maestro CLI and connects to the emulator over ADB.
4. It downloads the APK and installs it on the emulator with `adb install`.
5. Maestro runs every flow in `maestro/`. JUnit report, screenshots and screen recordings are saved as artifacts.
6. Testkube deletes the emulator pod and the test pod.

## Run the flows locally

With an emulator running and the app installed:

```sh
cd mobile/maestro
maestro test .
```
