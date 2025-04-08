-- Use your existing database
USE attendance_db;
CREATE TABLE students (
    id INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    encoding LONGTEXT NOT NULL
);


CREATE TABLE attendance (
    id INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
    student_id INT(11),
    date DATE,
    time TIME,
    timestamp DATETIME NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id)
);


