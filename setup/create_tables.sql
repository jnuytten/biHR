CREATE TABLE calendar_workday (
    employee_id INT NOT NULL,
    date DATE NOT NULL,
    scheduled_time INT DEFAULT 0,
    training_time INT DEFAULT 0,
    vacation_time INT DEFAULT 0,
    holiday_time INT DEFAULT 0,
    adv_time INT DEFAULT 0,
    extralegal_vacation_time INT DEFAULT 0,
    paid_leave_time_total INT DEFAULT 0,
    unpaid_leave_time_total INT DEFAULT 0,
    paid_sick_time INT DEFAULT 0,
    unpaid_sick_time INT default 0,
    sick_time_total INT default 0, 
    PRIMARY KEY (employee_id, date)
);
CREATE TABLE calendar_saldi (
    employee_id INT NOT NULL,
    training INT DEFAULT 0,
    vacation INT DEFAULT 0,
    holiday INT DEFAULT 0,
    adv INT DEFAULT 0,
    extralegal_vacation INT DEFAULT 0,
    sickness INT DEFAULT 0, 
    PRIMARY KEY (employee_id)
);
CREATE TABLE people_workers (
    id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    role_name VARCHAR(255) NOT NULL,
    team VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
);
CREATE TABLE people_employee_contracts (
    id INT NOT NULL,
    employee_id INT NOT NULL,
    function_category VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    monthly_salary DOUBLE(10,4) NOT NULL,
    mobility_type VARCHAR(55) NOT NULL,
    monthly_mobility FLOAT NOT NULL,
    fte FLOAT NOT NULL,
    PRIMARY KEY (id)
);
CREATE TABLE projects (
    id INT NOT NULL AUTO_INCREMENT,
    client VARCHAR(255) NOT NULL,
    msp_percentage FLOAT DEFAULT 0,
    start_date DATE NOT NULL,
    end_date DATE,
    percentage FLOAT NOT NULL,
    hourly_rate DOUBLE(10,4) NOT NULL,
    employee_id INT NOT NULL
    PRIMARY KEY (id)
);
CREATE TABLE people_freelance_contracts (
    id INT NOT NULL AUTO_INCREMENT,
    employee_id INT NOT NULL,
    hourly_rate DOUBLE(10,4) NOT NULL,
    PRIMARY KEY (id)
);
