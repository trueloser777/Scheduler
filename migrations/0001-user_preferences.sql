-- User preferences 
-- depends: 0000-initialization

CREATE TABLE user_preferences (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE PRIMARY KEY,
    notification_interval INTERVAL DEFAULT '1 hour' NOT NULL,
    graphic_schedule BOOLEAN DEFAULT TRUE NOT NULL,
    text_schedule BOOLEAN DEFAULT TRUE NOT NULL,

    CHECK(notification_interval <= INTERVAL '6 hours')
);


CREATE FUNCTION add_default_user_preferences__trigger()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_preferences(user_id)
        VALUES(NEW.id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER add_default_user_preferences__trigger
    AFTER INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION add_default_user_preferences__trigger();

