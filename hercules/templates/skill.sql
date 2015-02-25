DROP TABLE IF EXISTS `skill`;

CREATE TABLE IF NOT EXISTS `skill` (
  `char_id` INT(11) UNSIGNED NOT NULL DEFAULT '0',
  `id` SMALLINT(11) UNSIGNED NOT NULL DEFAULT '0',
  `lv` TINYINT(4) UNSIGNED NOT NULL DEFAULT '0',
  `flag` TINYINT(1) UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (`char_id`,`id`)
) ENGINE=InnoDB;

