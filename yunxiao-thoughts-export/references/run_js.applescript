on run argv
  set jsFile to item 1 of argv
  set js to read POSIX file jsFile
  tell application "Google Chrome"
    tell window id 1518279837
      set r to execute active tab javascript js
    end tell
  end tell
  return r
end run
