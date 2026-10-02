lead <- function(subteam, type = 1, active = 1){
  l1 <- (email %>% filter(Lead_TF == subteam))
  
  if (active == 3){l1 <- (email %>% filter(Lead == subteam))}
  
  l2 <- as.data.frame(l1 %>% select(Firstname, Lastname, Institution))

  ## a task force with no lead row yields an empty vector, not "NA NA (NA)"
  if (nrow(l2) == 0){return(character(0))}

  out <- character(nrow(l2))

  if (type == 1){
    for (k in seq_len(nrow(l2))){out[k] <- paste(paste(l2[k, 1:2], collapse = " "), " (", l2[k, 3], ")", sep = "")}}

  if (type == 2){
    for (k in seq_len(nrow(l2))){out[k] <- paste(paste(l2[k, 1:2], collapse = " "), ", ", l2[k, 3], sep = "")}}

  return(out)
}
